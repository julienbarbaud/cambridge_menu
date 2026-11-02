import calendar
import io
import itertools
import logging
import re
from datetime import date, timedelta
import pdfplumber
from pdfplumber.utils.text import extract_text
import requests
import bs4
from model import Dish
from util import fetch_html, dishes_sample_printer, WEEKDAYS

LOGGER = logging.getLogger(__name__)

# Word gaps in this PDF are only a few points wide and there are no space characters in it.
# Below ~1.5 words get cut in two, above ~2 they get glued together.
WORD_GAP = 1.5
# The menu is typed in small caps: a capital is drawn at full size, a lowercase letter as a
# smaller capital. Draw the letters back in lowercase so "POTATO PANCAKES" is "Potato pancakes".
RESTORE_CASE = True
SMALL_CAPS_RATIO = 0.95
# Pudding and sides are listed once for the whole day; the meals they get attached to.
SHARED_ROW_MEALS = ("lunch", "dinner")
MAX_DAYS_FROM_TODAY = 150  # a week-commencing date further away than this is a typo

# row label in the PDF -> course
COURSES = {
    "main dish": "mains",
    "alternative dish": "alternative",
    "allergen friendly dish": "allergen friendly",
    "pudding": "dessert",
    "sides": "sides",
}

BASE_URL = "https://www.pem.cam.ac.uk/college/catering/information-students/servery-menu"

SHARED_ROWS = {"pudding", "sides"}
# the table has two blocks of (main, alternative, allergen friendly) rows, but doesn't label them
BLOCK_MEALS = ("lunch", "dinner")

MONTHS = [name.lower() for name in calendar.month_name[1:]]
WEEK_DATE_RE = re.compile(r"(\d{1,2})\s*(?:st|nd|rd|th)?\s*(" + "|".join(MONTHS) + ")", re.IGNORECASE)


def get_menu_pdfs() -> list[tuple[str, str]]:
    """TODO: return [(pdf_url, 'Weeks commencing 05th October, 26th October,16th November'), ...],
    one entry per PDF (the menu repeats on a 3-week rota, so there is a PDF per rota week)."""
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    pdf_links = soup.select('div.embedded-entity[data-entity-type="file"] a')
    paragraphs = [p.get_text(strip=True).lower() for p in soup.select("div.field.field--name-body p")]
    urls = [str(link.attrs["href"]) for link in pdf_links]
    weeks_labels = [text for text in paragraphs if re.match("week.*commencing", text)]
    return list(zip(urls, weeks_labels))



def scrape_pembroke(college_name: str = "Pembroke") -> list[Dish]:
    dishes = []
    for url, weeks_label in get_menu_pdfs():
        try:
            week_starts = parse_weeks_commencing(weeks_label)
            dishes.extend(parse_pdf(fetch_html(url), college_name, week_starts))
        except Exception:
            LOGGER.exception(f"{college_name}: could not read {url}")
    if not dishes:
        raise RuntimeError(f"no data for {college_name}")
    return dishes


def parse_weeks_commencing(label: str, today: date | None = None) -> list[date]:
    """'Weeks commencing 05th October, 26th October,16th November' -> the three Mondays. The label
    has no year, so pick the year that makes each date a Monday close to today."""
    today = today or date.today()
    matches = WEEK_DATE_RE.findall(label)
    if not matches:
        raise ValueError(f"Pembroke: no dates found in {label!r}")
    week_starts = []
    for day_text, month_text in matches:
        day, month = int(day_text), MONTHS.index(month_text.lower()) + 1
        candidates = []
        for year in (today.year - 1, today.year, today.year + 1):
            try:
                candidate = date(year, month, day)
            except ValueError:
                continue
            if candidate.weekday() == 0 and abs((candidate - today).days) <= MAX_DAYS_FROM_TODAY:
                candidates.append(candidate)
        if not candidates:
            raise ValueError(f"Pembroke: '{day_text} {month_text}' isn't a Monday within {MAX_DAYS_FROM_TODAY} days of today")
        week_starts.append(min(candidates, key=lambda candidate: abs((candidate - today).days)))
    return week_starts


def parse_pdf(source: bytes | str, college_name: str, week_starts: list[date]) -> list[Dish]:
    """The PDF is one rota week's menu; it applies to every week in week_starts."""
    for week_start in week_starts:
        if week_start.weekday() != 0:
            raise ValueError(f"Pembroke: week start {week_start} is not a Monday")
    pdf_file = io.BytesIO(source) if isinstance(source, bytes) else source
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[0]
        table = find_menu_table(page)
        menu = read_menu(page, table)  # {weekday: {meal: [(course, name), ...]}}

    dishes = []
    for week_start in week_starts:
        for weekday, meals in menu.items():
            day = week_start + timedelta(days=WEEKDAYS.index(weekday))
            for meal_type, items in meals.items():
                for course, name in items:
                    dishes.append(Dish(
                        course=course,
                        name=name,
                        meal_type=meal_type,
                        date=day.isoformat(),
                        college=college_name,
                    ))
    if not dishes:
        raise ValueError(f"{college_name}: empty menu")
    return dishes


def find_menu_table(page):
    tables = page.find_tables()
    if not tables:
        raise ValueError("Pembroke: no table found in the PDF")
    table = max(tables, key=lambda table: len(table.rows))
    if len(table.rows) < 8:
        raise ValueError(f"Pembroke: table has {len(table.rows)} rows, layout may have changed")
    return table


def read_menu(page, table) -> dict[str, dict[str, list[tuple[str | None, str]]]]:
    day_columns = read_day_columns(page, table.rows[0])
    menu: dict[str, dict[str, list]] = {weekday: {} for weekday in WEEKDAYS}
    shared: dict[str, list] = {weekday: [] for weekday in WEEKDAYS}
    block = -1

    for row in table.rows[1:]:
        if row.cells[0] is None:
            continue
        label = " ".join(paragraphs(page, row.cells[0])).lower()
        course = COURSES.get(label)
        if course is None:
            continue
        if label == "main dish":
            block += 1  # a new lunch/dinner block starts at its "main dish" row
            if block >= len(BLOCK_MEALS):
                raise ValueError("Pembroke: more than two lunch/dinner blocks, layout may have changed")
        elif block < 0:
            raise ValueError(f"Pembroke: row {label!r} before the first 'main dish' row")

        for cell in row.cells[1:]:
            if cell is None:
                continue
            names = paragraphs(page, cell, restore_case=RESTORE_CASE)
            if not names:
                continue
            weekdays = [weekday for weekday, (x0, x1) in day_columns.items() if cell[0] <= (x0 + x1) / 2 <= cell[2]]
            if "".join(names).replace(" ", "").lower() == "brunch":
                # the weekend "lunch" cells are merged into one "B R U N C H" box spanning Sat and Sun
                for weekday in weekdays:
                    menu[weekday]["brunch"] = [(None, "Brunch")]
                continue
            for weekday in weekdays:
                if label in SHARED_ROWS:
                    shared[weekday].extend((course, name) for name in names)
                else:
                    menu[weekday].setdefault(BLOCK_MEALS[block], []).extend((course, name) for name in names)
        if label == "sides":
            break  # what follows is the legend ("allergen friendly dish", "student special")

    if block != len(BLOCK_MEALS) - 1:
        raise ValueError(f"Pembroke: found {block + 1} lunch/dinner blocks, expected {len(BLOCK_MEALS)}")
    for weekday, items in shared.items():
        for meal_type in SHARED_ROW_MEALS:
            if menu[weekday].get(meal_type):
                menu[weekday][meal_type].extend(items)
    return {weekday: meals for weekday, meals in menu.items() if meals}


def read_day_columns(page, header_row) -> dict[str, tuple[float, float]]:
    """{'monday': (x0, x1), ...} read from the header row, so a stray empty column can't shift things."""
    columns = {}
    for cell in header_row.cells:
        if cell is None:
            continue
        text = " ".join(paragraphs(page, cell)).lower()
        if text in WEEKDAYS:
            columns[text] = (cell[0], cell[2])
    missing = [weekday for weekday in WEEKDAYS if weekday not in columns]
    if missing:
        raise ValueError(f"Pembroke: no column for {missing} in the table header")
    return columns


def paragraphs(page, bbox, restore_case: bool = False) -> list[str]:
    """One string per paragraph in the cell. The PDF is tagged, and every paragraph (a dish, even a
    wrapped one) has its own marked-content id; lines are not enough to tell a wrapped dish
    from two dishes."""
    x0, top, x1, bottom = bbox
    # cell boxes can stick out of the page by a fraction of a point, which crop() rejects
    chars = page.crop((max(x0, 0), max(top, 0), min(x1, page.width), min(bottom, page.height))).chars
    if chars and all(char.get("mcid") is None for char in chars):
        raise ValueError("Pembroke: PDF has no paragraph tags, can't split dishes")
    if restore_case and chars:
        capital_size = max(char["size"] for char in chars)
        chars = [
            char if char["size"] >= capital_size * SMALL_CAPS_RATIO else {**char, "text": char["text"].lower()}
            for char in chars
        ]
    out = []
    for _, group in itertools.groupby(chars, key=lambda char: char.get("mcid")):
        text = " ".join(extract_text(list(group), x_tolerance=WORD_GAP).split())
        if text:
            out.append(text)
    return out


if __name__ == "__main__":
    dishes = scrape_pembroke()
    dishes_sample_printer(dishes)
