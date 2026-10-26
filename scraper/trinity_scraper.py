import io
import bs4
import itertools
import re
import sys
from datetime import date, timedelta
import pdfplumber
from dateutil import parser
import logging

from model import Dish
from util import fetch_html, normalize_string_data, MEAL_MARKERS

#TODO: scrape pdf menu url from trinity website
WEBSITE_URL= "https://www.trin.cam.ac.uk/download/hall-menu-this-week/"
LOGGER = logging.getLogger(__name__)

def get_menu_pdf_url():
    html = fetch_html(WEBSITE_URL)
    link = bs4.BeautifulSoup(html, "html.parser").find("a", class_="inddl")
    if link is None:
        raise RuntimeError("No links found on the Trinity website for their menu")
    pdf_url = link.get("href")
    if pdf_url is None:
        raise RuntimeError("can't find Trinity menu url in the link")
    return str(pdf_url)

# "Mains", "Mains:", "Dessert: Banoffee Pie Sundae", "Daily Special: (vegan)"
# The name must be followed by a colon or the end of the text, so a dish that merely
# starts with one of these words ("Dessert Pizza") is not mistaken for a header.
COURSE_RE = re.compile(
    r"^(starter soup|mains|sides|daily special|dessert)\s*(?::\s*(.*))?$", re.IGNORECASE
)
# text that is only dietary tags, e.g. "(v)(vegan)" or "(wf/df)"
TAGS_ONLY_RE = re.compile(r"^(\s*\((?:v|vegan|wf/df|gf|wf|df)\)\s*)+$", re.IGNORECASE)


def scrape_trinity(college_name: str) -> list[Dish]:
    url = get_menu_pdf_url()
    if not url:
        raise ValueError("MENU_PDF_URL is not set")
    pdf_bytes = fetch_html(url)  # returns raw bytes, fine for a PDF too
    return parse_pdf(pdf_bytes, college_name)


def parse_pdf(source: bytes | str, college_name: str) -> list[Dish]:
    pdf_file = io.BytesIO(source) if isinstance(source, bytes) else source
    dishes = []
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[0]
        week_end = parse_week_ending(page.extract_text() or "")
        table = find_menu_table(pdf)
        headers = table.extract()[0]
        day_cells = table.rows[1].cells
        for i, (header, cell) in enumerate(zip(headers, day_cells)):
            date = week_end - timedelta(days=6 - i)
            check_header(header, date)
            paras = merge_split_paragraphs(paragraphs(page, cell))
            dishes.extend(parse_day(paras, date, college_name))
    if not dishes:
        raise ValueError("empty menu for Trinity")
    return dishes


def parse_week_ending(page_text: str) -> date:
    m = re.search(r"WEEK ENDING\s+(.+?\d{4})", page_text, re.IGNORECASE)
    if m is None:
        raise ValueError("Trinity: can't find 'WEEK ENDING <date>' title")
    try:
        return parser.parse(m.group(1)).date()
    except ValueError:
        raise ValueError(f"Trinity: can't parse week ending date {m.group(1)!r}")


def find_menu_table(pdf):
    for page in pdf.pages:
        for table in page.find_tables():
            if len(table.rows) >= 2 and len(table.rows[0].cells) == 7:
                return table
    raise ValueError("Trinity: no 7-column menu table found, layout may have changed")


def check_header(header: str | None, date: date) -> None:
    text = (header or "").lower()
    if date.strftime("%A").lower() not in text or str(date.day) not in text:
        raise ValueError(
            f"Trinity: column header {header!r} doesn't match expected {date:%A %d}"
        )


def paragraphs(page, cell) -> list[str]:
    chars = page.crop(cell).chars
    if chars and all(c.get("mcid") is None for c in chars):
        raise ValueError("Trinity: PDF has no paragraph tags, can't split dishes")
    out = []
    for _, group in itertools.groupby(chars, key=lambda c: c.get("mcid")):
        text = " ".join("".join(c["text"] for c in group).split())
        if text:
            out.append(text)
    return out


def merge_split_paragraphs(paras: list[str]) -> list[str]:
    merged: list[str] = []
    carry = ""
    for text in paras:
        text = f"{carry} {text}".strip() if carry else text
        if text.endswith(("-", "–")):
            carry = text
            continue
        carry = ""
        merged.append(text)
    if carry:
        merged.append(carry)
    return merged


def parse_day(paras: list[str], date: date, college_name: str) -> list[Dish]:
    dishes: list[Dish] = []
    meal: str | None = None
    course: str | None = None

    def add(name: str) -> None:
        dishes.append(Dish(
            course=course,
            name=name,
            meal_type=meal,  # type: ignore  # checked before add() is called
            date=date.isoformat(),
            college=college_name,
        ))

    for text in paras:
        if text.lower() in MEAL_MARKERS:
            # Sunday's cell reads "LUNCH" then "BRUNCH"; the later marker wins,
            # and no dishes sit between them
            meal = normalize_string_data(text)
            course = None
            continue
        header = COURSE_RE.match(text)
        if header:
            course = normalize_string_data(header.group(1))
            rest = (header.group(2) or "").strip()
            # tags on a header ("Starter Soup: (v)") describe the course, not a dish
            if rest and not TAGS_ONLY_RE.match(rest):
                if meal is not None:
                    add(rest)
            continue
        if TAGS_ONLY_RE.match(text):
            continue
        if text.startswith("("):
            # a note about the dish above, e.g. "(Maple Burger Roll, Gerkin Slices, ...)"
            continue
        if meal is None or course is None:
            logging.warning(f"Trinity: dish outside a meal/course on {date:%d %b}: {text!r}")
            continue
        add(text)
    return dishes


if __name__ == "__main__":
    scrape_trinity("Trinity")
