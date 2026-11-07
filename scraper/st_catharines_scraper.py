import io
import logging
import re
from datetime import date, timedelta
import bs4

import pdfplumber

from model import Dish
from util import fetch_html, dishes_sample_printer, normalize_string_data, WEEKDAYS, MEAL_MARKERS


LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.caths.cam.ac.uk"
CATERING_URL = "https://www.caths.cam.ac.uk/students/college-facilities-and-forms/catering-for-our-community/cafeteria"

MAX_DAYS_FROM_TODAY = 150  
MAX_DAYS_PAST = 14


WORD_GAP = 1.5  # max gap in points between letters of a word
LINE_GAP = 3  # words whose tops differ by less than this are on the same line
LABEL_COLUMN_RIGHT = 147  # "Counter N" labels end by x=135 and dish text starts at x=160 or later
                          # (position is used, not font size: one label is set at 11pt instead of 12pt)
BULLET_MAX_SIZE = 10  # the bullet before each main dish is a 3.8pt filled circle
BULLET_TO_TEXT_MAX = 40  # how far left of its text a bullet can be
MAX_DAYS_FROM_TODAY = 180  # a Monday further away than this is a typo
# True: course "counter 1" holds that counter's main dish followed by its sides.
# False: course "mains" and "sides" across all counters.
GROUP_BY_COUNTER = True

# "(28.09/26.10/23.11)": the Mondays the menu covers (dd.mm, optionally dd.mm.yyyy)
DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?")


def get_menu_pdfs() -> list[str]:
    html = fetch_html(CATERING_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    menus_container = None
    for content_container in soup.select("div.content"):
        potential_headers = content_container.find_all("h2", recursive=True)
        for potential_header in potential_headers:
            header_text = potential_header.get_text(strip=True).lower()
            # selecting the links about meals
            # have to be careful, links include a "price list for lunch/dinner" to exclude
            if "menu" in header_text:
                menus_container = content_container
                break
        if menus_container:
            break
    if menus_container is None:
        raise RuntimeError("Can not find the menus on the webpage")
    urls = []
    for link in menus_container.find_all("a"):
        text = link.get_text(strip=True).lower()
        if any([((marker in text or "weekend" in text) and not re.search(r"prices?\s+list", text)) for marker in MEAL_MARKERS]):
            try:
                urls.append(f"{BASE_URL}{link['href']}")
            except:
                LOGGER.warning(f"link for {text} is not pointing to any reference")
    if not link:
        raise RuntimeError("Can not find any link to pdf menus")
    return urls


def scrape_st_catharines(college_name: str = "St Catharine's") -> list[Dish]:
    dishes = []
    for url in get_menu_pdfs():
        try:
            dishes.extend(parse_pdf(fetch_html(url), college_name))
        except Exception:
            LOGGER.exception(f"{college_name}: could not read {url}")
    if not dishes:
        raise RuntimeError(f"no data for {college_name}")
    return dishes


def parse_pdf(source: bytes | str, college_name: str, today: date | None = None) -> list[Dish]:
    """One PDF = one meal (lunch, or dinner) for the days it lists, for every week in its title."""
    pdf_file = io.BytesIO(source) if isinstance(source, bytes) else source
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[0]
        # a hidden leftover "WEDNESDAY" sits off the left edge of every file; only look at the page
        words = [
            word for word in page.extract_words(x_tolerance=WORD_GAP, extra_attrs=["fontname", "size"])
            if word["x0"] >= 0 and word["x1"] <= page.width
        ]
        bullets = [
            curve for curve in page.curves
            if curve["x1"] - curve["x0"] < BULLET_MAX_SIZE and curve["bottom"] - curve["top"] < BULLET_MAX_SIZE
        ]

    headings = sorted(
        (word["top"], word["text"].lower()) for word in words
        if "playfair" in word["fontname"].lower() and "bold" in word["fontname"].lower()
        and word["text"].lower() in WEEKDAYS
    )
    if not headings:
        raise ValueError("St Catharine's: no weekday headings found")
    first_top = headings[0][0]

    title = " ".join(word["text"] for word in sorted(words, key=lambda word: (round(word["top"]), word["x0"])) if word["top"] < first_top)
    meal_type = meal_type_from_title(title)
    week_starts = parse_week_starts(title, today)

    below = [word for word in words if word["top"] >= first_top and "montserrat" in word["fontname"].lower()]
    labels = cluster_lines([word for word in below if word["x1"] <= LABEL_COLUMN_RIGHT])
    lines = cluster_lines([word for word in below if word["x1"] > LABEL_COLUMN_RIGHT])
    if not bullets:
        raise ValueError("St Catharine's: no bullets found, can't tell where each dish starts")

    def day_of(top: float) -> int:
        return max(index for index, (heading_top, _) in enumerate(headings) if heading_top <= top)

    blocks: list[list[list[dict]]] = [[] for _ in headings]  # per day: one list of lines per counter
    for line in lines:
        day = day_of(line["top"])
        if starts_with_bullet(line, bullets):
            blocks[day].append([line])
        elif blocks[day]:
            blocks[day][-1].append(line)
        else:
            LOGGER.warning(f"{college_name}: text before the first dish of {headings[day][1]}: {line['text']!r}")
    labels_by_day: list[list[dict]] = [[] for _ in headings]
    for label in labels:
        labels_by_day[day_of(label["top"])].append(label)

    entries = []  # (weekday, course, name), in menu order
    for day, (_, weekday) in enumerate(headings):
        if len(blocks[day]) != len(labels_by_day[day]):
            LOGGER.warning(
                f"St Catharine's: {len(blocks[day])} dishes but {len(labels_by_day[day])} counter labels on {weekday}"
            )
            continue
        for label, block in zip(labels_by_day[day], blocks[day]):
            paragraphs = join_wrapped([line["text"] for line in block])
            if len(paragraphs) > 2:
                LOGGER.warning(f"{college_name}: {weekday} {label['text']}: expected a dish and a sides line, got {paragraphs}")
            main = paragraphs[0]
            sides = [side.strip() for text in paragraphs[1:] for side in text.split(",") if side.strip()]
            counter = normalize_string_data(label["text"])
            entries.append((weekday, counter if GROUP_BY_COUNTER else "mains", main))
            entries.extend((weekday, counter if GROUP_BY_COUNTER else "sides", side) for side in sides)

    dishes = [
        Dish(
            course=course,
            name=name,
            meal_type=meal_type,
            date=(week_start + timedelta(days=WEEKDAYS.index(weekday))).isoformat(),
            college=college_name,
        )
        for week_start in week_starts
        for weekday, course, name in entries
    ]
    if not dishes:
        raise ValueError(f"{college_name}: empty menu")
    return dishes


def cluster_lines(words: list[dict]) -> list[dict]:
    """Group words into lines, top to bottom: [{'text', 'top', 'x0'}]."""
    clusters: list[list[dict]] = []
    for word in sorted(words, key=lambda word: word["top"]):
        if clusters and abs(word["top"] - clusters[-1][0]["top"]) < LINE_GAP:
            clusters[-1].append(word)
        else:
            clusters.append([word])
    lines = []
    for cluster in clusters:
        cluster.sort(key=lambda word: word["x0"])
        lines.append({
            "text": " ".join(word["text"] for word in cluster),
            "top": cluster[0]["top"],
            "center": (cluster[0]["top"] + cluster[0]["bottom"]) / 2,
            "x0": cluster[0]["x0"],
        })
    return lines


def starts_with_bullet(line: dict, bullets: list[dict]) -> bool:
    """The main dish of each counter is the line with a bullet drawn just left of it."""
    return any(
        abs((bullet["top"] + bullet["bottom"]) / 2 - line["center"]) <= 4
        and 0 < line["x0"] - bullet["x1"] <= BULLET_TO_TEXT_MAX
        for bullet in bullets
    )


def join_wrapped(lines: list[str]) -> list[str]:
    """A line starting in lower case continues the previous one (a long dish wrapped onto two lines)."""
    paragraphs: list[str] = []
    for line in lines:
        if paragraphs and line[0].islower():
            paragraphs[-1] = f"{paragraphs[-1]} {line}"
        else:
            paragraphs.append(line)
    return paragraphs


def meal_type_from_title(title: str) -> str:
    """'Week 1 - Lunch Cafeteria Menu' -> lunch; 'Weekend 1 - Dinner Cafeteria Menu' -> dinner."""
    meals = {
        "lunch" if word == "lunch" else "dinner"
        for word in re.findall(r"(?<![a-z])(lunch|dinner|supper)(?![a-z])", title.lower())
    }
    if len(meals) != 1:
        raise ValueError(f"St Catharine's: can't tell lunch from dinner in the title {title!r}")
    return meals.pop()


def parse_week_starts(title: str, today: date | None = None) -> list[date]:
    """'(28.09/26.10/23.11)' -> the three Mondays. The year is not given (unless dd.mm.yyyy is), so pick
    the year that makes each date a Monday close to today. A date that isn't one is rejected."""
    today = today or date.today()
    matches = DATE_RE.findall(title)
    if not matches:
        raise ValueError(f"St Catharine's: no dates (dd.mm) found in the title {title!r}")
    week_starts = set()
    for day_text, month_text, year_text in matches:
        day, month = int(day_text), int(month_text)
        year = int(year_text) + (2000 if len(year_text) == 2 else 0) if year_text else None
        candidates = []
        for candidate_year in [year] if year else [today.year - 1, today.year, today.year + 1]:
            try:
                candidate = date(candidate_year, month, day)
            except ValueError:
                continue
            if candidate.weekday() == 0 and abs((candidate - today).days) <= MAX_DAYS_FROM_TODAY:
                candidates.append(candidate)
        if not candidates:
            raise ValueError(f"St Catharine's: '{day_text}.{month_text}' isn't a Monday within {MAX_DAYS_FROM_TODAY} days of today")
        week_starts.add(min(candidates, key=lambda candidate: abs((candidate - today).days)))
    return sorted(week_starts)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    dishes = scrape_st_catharines()
    dishes_sample_printer(dishes)
