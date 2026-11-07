# DISCALIMER: the pdf scraping part is mostly AI-generated

import calendar
import io
import itertools
import logging
import re
from datetime import date, timedelta
from urllib.parse import unquote

import bs4
import pdfplumber
from pdfplumber.utils.text import extract_text

from model import Dish
from util import fetch_html, dishes_sample_printer, normalize_string_data, WEEKDAYS

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://my.st-edmunds.cam.ac.uk/category/menus/"

WORD_GAP = 1.5
MAX_DAYS_FROM_TODAY = 150  # a week-commencing date further away than this is a typo
MAX_DAYS_PAST = 14

MONTH_PREFIXES = [name[:3].lower() for name in calendar.month_name[1:]]
# "2nd November", "2 Nov", "2nd of November 2026"
DATE_RE = re.compile(r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:of\s+)?([a-z]{3,9})\b(?:\s*,?\s*(\d{4}))?", re.IGNORECASE)
KCAL_RE = re.compile(r"\d+\s*kcal", re.IGNORECASE)
KCAL_AT_END_RE = re.compile(r"\d+\s*kcal\s*$", re.IGNORECASE)
TIME_RE = re.compile(r"\d{1,2}[:.]\d{2}\s*[–-]\s*\d{1,2}[:.]\d{2}")
# a diet tag that ended up in a paragraph of its own, e.g. the "(Vg)" after a long dish name
DIET_TAG_RE = re.compile(r"\(?(v|vg|ve|vegan|vegetarian)\)?", re.IGNORECASE)


def get_menu_pdfs() -> dict:
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    week_rows = soup.select("div.main div.container div.row article.card div.row div.entry-content")
    weeks_paragraphs = [row.find("p") for row in week_rows]
    # there is typically two links per week (one for lunch, one for supper)
    links = [row.select("a.pdfemb-viewer") for row in week_rows]
    url_label_map = {}
    for row, lunch_supper_links in zip(weeks_paragraphs, links):
        label = row.get_text(strip=True).lower() if row else ""
        urls = [link.attrs["href"] for link in lunch_supper_links if link and "href" in link.attrs]
        url_label_map[label] = urls
    return url_label_map


def scrape_st_edmunds(college_name: str = "St Edmund's") -> list[Dish]:
    today = date.today()
    dishes = []
    for label, urls in get_menu_pdfs().items():
        try:
            week_start = parse_week_start(label, today)
        except ValueError:
            LOGGER.exception(f"{college_name}: unreadable week label {label!r}")
            continue
        if (today - week_start).days > MAX_DAYS_PAST:
            continue
        for url in urls:
            try:
                meal_type = meal_type_from_text(unquote(url).rsplit("/", 1)[-1])
                dishes.extend(parse_pdf(fetch_html(url), college_name, week_start, meal_type))
            except Exception:
                LOGGER.exception(f"{college_name}: could not read {url}")
    if not dishes:
        raise RuntimeError(f"no data for {college_name}")
    return dishes


def parse_week_start(label: str, today: date | None = None) -> date:
    """'Weekly Menus – Week Commencing 2nd November' -> the Monday. Tolerates other wording and
    abbreviations, but fails if there is no date, more than one date, or the date is not a Monday
    close to today (a typo). The year is only used if the label has one."""
    today = today or date.today()
    found = set()
    for day, word, year in DATE_RE.findall(label):
        prefix = word[:3].lower()
        if prefix in MONTH_PREFIXES:
            found.add((int(day), MONTH_PREFIXES.index(prefix) + 1, int(year) if year else None))
    if not found:
        raise ValueError(f"St Edmund's: no date found in {label!r}")
    if len(found) > 1:
        raise ValueError(f"St Edmund's: several dates in {label!r}")
    day, month, year = found.pop()
    candidates = []
    for candidate_year in [year] if year else [today.year - 1, today.year, today.year + 1]:
        try:
            candidate = date(candidate_year, month, day)
        except ValueError:
            continue
        if candidate.weekday() == 0 and abs((candidate - today).days) <= MAX_DAYS_FROM_TODAY:
            candidates.append(candidate)
    if not candidates:
        raise ValueError(f"St Edmund's: {label!r} isn't a Monday within {MAX_DAYS_FROM_TODAY} days of today")
    return min(candidates, key=lambda candidate: abs((candidate - today).days))


def meal_type_from_text(text: str) -> str | None:
    """'lunch' or 'dinner' (supper counts as dinner); None if neither or both are mentioned."""
    words = set(re.findall(r"(?<![a-z])(lunch|supper|dinner)(?![a-z])", text.lower()))
    meals = {"lunch" if word == "lunch" else "dinner" for word in words}
    return meals.pop() if len(meals) == 1 else None


def parse_pdf(source: bytes | str, college_name: str, week_start: date, meal_type: str | None = None) -> list[Dish]:
    """meal_type is what the URL said; the PDF's own "LUNCH MENU" / "DINNER MENU" title is checked
    against it. In the lunch PDF the Saturday column is brunch."""
    if week_start.weekday() != 0:
        raise ValueError(f"St Edmund's: week start {week_start} is not a Monday")
    pdf_file = io.BytesIO(source) if isinstance(source, bytes) else source
    entries = []  # (weekday index, y position, meal, course, name)
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[0]
        header_meal = meal_type_from_text(" ".join(re.findall(r"(?:lunch|dinner|supper)\s+menu", (page.extract_text() or "").lower())))
        if meal_type and header_meal and meal_type != header_meal:
            raise ValueError(f"St Edmund's: URL says {meal_type} but the PDF title says {header_meal}")
        meal_type = meal_type or header_meal
        if meal_type is None:
            raise ValueError("St Edmund's: can't tell if this is the lunch or the dinner menu")

        table = find_menu_table(page)
        centers = weekday_centers(page, table.bbox[1])
        for row in table.rows:
            for cell in row.cells:
                if cell is None:
                    continue
                weekdays = [weekday for weekday, center in centers.items() if cell[0] <= center <= cell[2]]
                if not weekdays:
                    continue  # a sliver of a merged cell
                paras = cell_paragraphs(page, cell)
                is_brunch = any(text.lower() == "brunch" for text, _ in paras)
                names = brunch_dishes(paras) if is_brunch else dish_names(paras)
                course = course_label(page, table.bbox[0], cell)
                for weekday in weekdays:
                    for name in names:
                        entries.append((WEEKDAYS.index(weekday), cell[1], "brunch" if is_brunch else meal_type, course, name))

    entries.sort(key=lambda entry: (entry[0], entry[1]))  # by day, then top to bottom
    dishes = [
        Dish(course=course, name=name, meal_type=meal, date=(week_start + timedelta(days=day)).isoformat(), college=college_name)
        for day, _, meal, course, name in entries
    ]
    if not dishes:
        raise ValueError(f"{college_name}: empty menu")
    return dishes


def find_menu_table(page):
    tables = page.find_tables()
    if not tables:
        raise ValueError("St Edmund's: no table found in the PDF")
    table = max(tables, key=lambda table: (table.bbox[2] - table.bbox[0]) * (table.bbox[3] - table.bbox[1]))
    if len(table.rows) < 4:
        raise ValueError(f"St Edmund's: table has {len(table.rows)} rows, layout may have changed")
    return table


def weekday_centers(page, table_top: float) -> dict[str, float]:
    """x position of each weekday heading above the table; the table's columns are matched to days by it."""
    centers = {}
    for word in page.extract_words(x_tolerance=WORD_GAP):
        text = word["text"].lower()
        if text in WEEKDAYS and word["bottom"] <= table_top + 2:
            centers[text] = (word["x0"] + word["x1"]) / 2
    if not centers:
        raise ValueError("St Edmund's: no weekday headings found above the table")
    return centers


def clamp(page, bbox):
    # cell boxes can stick out of the page by a fraction of a point, which crop() rejects
    return (max(bbox[0], 0), max(bbox[1], 0), min(bbox[2], page.width), min(bbox[3], page.height))


def join_text(chars) -> str:
    return " ".join(extract_text(chars, x_tolerance=WORD_GAP).split()) if chars else ""


def cell_paragraphs(page, bbox) -> list[tuple[str, str]]:
    """[(full text, bold text)] per paragraph. The PDF is tagged and every paragraph has its own
    marked-content id. A dish name is bold; calories and descriptions are italic or regular."""
    chars = page.crop(clamp(page, bbox)).chars
    if chars and all(char.get("mcid") is None for char in chars):
        raise ValueError("St Edmund's: PDF has no paragraph tags, can't split dishes")
    paras = []
    for _, group in itertools.groupby(chars, key=lambda char: char.get("mcid")):
        group = list(group)
        text = join_text(group)
        if text:
            paras.append((text, join_text([char for char in group if "bold" in char["fontname"].lower()])))
    return paras


def strip_kcal(name: str) -> str:
    return re.sub(r"\s*\d+\s*kcal\s*$", "", name, flags=re.IGNORECASE).strip()


def dish_names(paras: list[tuple[str, str]]) -> list[str]:
    names: list[str] = []
    for text, bold in paras:
        name = bold
        if KCAL_AT_END_RE.search(text):
            # the calorie count is in the same paragraph, and its first digit can be set in bold
            # ("Kecap Manis Noodles 1" + "70Kcal")
            name = re.sub(r"[\s\d]+$", "", name)
        name = strip_kcal(name)
        if not name:
            continue  # calories and descriptions have no bold text
        if DIET_TAG_RE.fullmatch(name) and names:
            names[-1] += f" {name}"
        else:
            names.append(name)
    return names


def brunch_dishes(paras: list[tuple[str, str]]) -> list[str]:
    """The brunch box prints its items in regular type, so here every paragraph that isn't the
    heading, the opening times or a calorie count is a dish."""
    names = []
    for text, _ in paras:
        if text.lower() == "brunch" or TIME_RE.fullmatch(text) or KCAL_RE.fullmatch(text):
            continue
        name = strip_kcal(text)
        if name:
            names.append(name)
    return names


def course_label(page, table_left: float, cell) -> str | None:
    """The dinner menu labels its rows (SOUP, MAINS, ...) in a column left of the table; the lunch
    menu has no labels."""
    if table_left < 5:
        return None
    left = (0, max(cell[1], 0), table_left - 1, min(cell[3], page.height))
    label = join_text(page.crop(clamp(page, left)).chars)
    return normalize_string_data(label) if label else None


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    dishes = scrape_st_edmunds()
    dishes_sample_printer(dishes)
