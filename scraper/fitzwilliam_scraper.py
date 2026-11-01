# DISCLAIMER: this script was 90% AI-written because I didn't want to learn how to parse a PDF
import bs4
import calendar
import io
import logging
import re
import sys
from datetime import date, timedelta
from urllib.parse import unquote, urljoin

import pdfplumber

from model import Dish
from util import fetch_html, dishes_sample_printer, MEAL_MARKERS, WEEKDAYS

LOGGER = logging.getLogger(__name__)
PAGE_URL = "https://www.fitz.cam.ac.uk/cafe-bar-and-buttery"

# Characters closer than this vertically are on the same line. A superscript ("26th")
# sits ~2pt off the baseline, while real line breaks are at least ~15pt apart.
LINE_TOLERANCE = 8
EXPECTED_BLOCKS = 14  # 7 days x (lunch + dinner)
MAX_DAYS_FROM_TODAY = 60  # a week-commencing date further away than this is a typo or a stale PDF

MONTHS = [name.lower() for name in calendar.month_name[1:]]
# "MONDAY LUNCH", "SATURDAY DINNER"
HEADING_RE = re.compile(
    r"^(" + "|".join(WEEKDAYS) + r")\s+(" + "|".join(MEAL_MARKERS) + r")$", re.IGNORECASE
)
# "Week Commencing 26th October"; the superscript can come out as "19 Octoberth", so no
# word boundary after the month
WEEK_RE = re.compile(
    r"week commencing\s+(\d{1,2})\s*(?:st|nd|rd|th)?\s*(" + "|".join(MONTHS) + ")",
    re.IGNORECASE,
)
# page furniture that appears after the last heading in the PDF's drawing order
NOT_A_DISH_RE = re.compile(
    r"^(buttery menu|week commencing\b.*|\(?v\)?\s*-\s*vegetarian|\(?vg\)?\s*-\s*vegan"
    r"|.*subject to change.*|https?://\S+|st|nd|rd|th)$",
    re.IGNORECASE,
)
# a dish never ends on one of these, so the next line must be its continuation
OPEN_ENDINGS = {"with", "&", "and", "or", "of", "in", "on", "a", "an", "the", "to", "for", "from", "served"}


def get_menu_pdf_urls() -> list[str]:
    """The College's food page links the current and next week's menu PDFs. The file names
    change every week, so find them by their link text. Formal Hall menus are excluded."""
    html = fetch_html(PAGE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    urls = []
    for link in soup.select("a[href]"):
        href = str(link["href"])
        name = unquote(href).lower()
        text = link.get_text(" ", strip=True).lower()
        if ".pdf" not in name or "formal" in name or "formal" in text:
            continue
        if "menu" in name or "menu" in text:
            urls.append(urljoin(PAGE_URL, href))
    urls = list(dict.fromkeys(urls))  # the same menu is linked twice on the page
    if not urls:
        raise RuntimeError("No buttery menu PDF links found on the Fitzwilliam website")
    return urls


def scrape_fitzwilliam(college_name: str = "Fitzwilliam") -> list[Dish]:
    dishes = []
    for url in get_menu_pdf_urls():
        try:
            dishes.extend(parse_pdf(fetch_html(url), college_name))
        except Exception:
            # e.g. next week's PDF is still a draft: keep the weeks that did parse
            LOGGER.exception(f"{college_name}: could not read {url}")
    if not dishes:
        raise RuntimeError(f"no data for {college_name}")
    return dishes


def parse_pdf(source: bytes | str, college_name: str, today: date | None = None) -> list[Dish]:
    pdf_file = io.BytesIO(source) if isinstance(source, bytes) else source
    with pdfplumber.open(pdf_file) as pdf:
        lines = [line for page in pdf.pages for line in page_lines(page)]
    week_start = parse_week_start(lines, today or date.today())
    blocks = split_blocks(lines)
    if len(blocks) != EXPECTED_BLOCKS:
        LOGGER.warning(f"{college_name}: found {len(blocks)} meals in the PDF, expected {EXPECTED_BLOCKS}")

    dishes = []
    for weekday, meal_type, block_lines in blocks:
        day = week_start + timedelta(days=WEEKDAYS.index(weekday))
        names = join_wrapped(block_lines)
        if len(names) == 1 and names[0].lower() == "brunch":
            meal_type = "brunch"  # the weekend "LUNCH" heading with a single "Brunch" item
        if not names:
            LOGGER.warning(f"{college_name}: no dishes for {weekday} {meal_type}")
        for name in names:
            dishes.append(Dish(
                course=None,
                name=name,
                meal_type=meal_type,
                date=day.isoformat(),
                college=college_name,
            ))
    if not dishes:
        raise ValueError(f"{college_name}: empty menu")
    return dishes


def page_lines(page) -> list[str]:
    """Text lines in the order the PDF draws them. That is not top-to-bottom: the menu is two
    columns, and each text box is drawn whole, so a heading is followed by its dishes
    (sorting by position would interleave the two columns line by line)."""
    lines: list[str] = []
    chars: list[str] = []
    line_top = None
    for char in page.chars:
        if line_top is not None and abs(char["top"] - line_top) > LINE_TOLERANCE:
            lines.append("".join(chars))
            chars, line_top = [], None
        if line_top is None:
            line_top = char["top"]
        chars.append(char["text"])
    if chars:
        lines.append("".join(chars))
    cleaned = (" ".join(line.split()) for line in lines)
    return [line for line in cleaned if line]


def parse_week_start(lines: list[str], today: date) -> date:
    """The PDF says 'Week Commencing 26th October' without a year. Pick the year that makes it a
    Monday close to today (this also copes with the New Year). A date that is not a Monday
    nearby, e.g. a typo like '27th October', is rejected instead of being filed under another year."""
    match = WEEK_RE.search(" ".join(lines))
    if match is None:
        raise ValueError("Fitzwilliam: can't find 'Week Commencing <date>' in the PDF")
    day = int(match.group(1))
    month = MONTHS.index(match.group(2).lower()) + 1
    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if candidate.weekday() == 0 and abs((candidate - today).days) <= MAX_DAYS_FROM_TODAY:
            candidates.append(candidate)
    if not candidates:
        raise ValueError(f"Fitzwilliam: {match.group(0)!r} isn't a Monday within {MAX_DAYS_FROM_TODAY} days of today")
    return min(candidates, key=lambda candidate: abs((candidate - today).days))


def split_blocks(lines: list[str]) -> list[tuple[str, str, list[str]]]:
    """[(weekday, meal, [lines of that meal])] from a heading to the next heading."""
    blocks: list[tuple[str, str, list[str]]] = []
    for line in lines:
        heading = HEADING_RE.match(line)
        if heading:
            blocks.append((heading.group(1).lower(), heading.group(2).lower(), []))
        elif blocks and not NOT_A_DISH_RE.match(line):
            blocks[-1][2].append(line)
    return blocks


def join_wrapped(lines: list[str]) -> list[str]:
    """The text boxes wrap long dishes onto a second line. Dishes start with a capital letter,
    so a line that starts in lower case continues the previous one."""
    dishes: list[str] = []
    for line in lines:
        if dishes and is_continuation(dishes[-1], line):
            dishes[-1] = f"{dishes[-1]} {line}"
        else:
            dishes.append(line)
    return dishes


def is_continuation(previous: str, line: str) -> bool:
    return (
        line[0].islower()
        or line[0] == "("  # a diet tag or note that wrapped onto its own line
        or previous.endswith((",", ":"))
        or previous.split()[-1].lower() in OPEN_ENDINGS
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s",
                        handlers=[logging.StreamHandler()])
    all_dishes = scrape_fitzwilliam()
    dishes_sample_printer(all_dishes)
