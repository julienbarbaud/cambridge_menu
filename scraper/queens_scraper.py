import bs4
import logging
from util import date_isoformat, fetch_html, dishes_sample_printer, normalize_string_data, MEAL_MARKERS
from model import Dish
from dateutil import parser
from datetime import datetime, timedelta

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.queens.cam.ac.uk/life-at-queens/catering/dining-hall/weekly-menu/"
weekday_map = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

def scrape_queens(college: str="Queen's"):
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    day_contents = soup.select("dl.accordion-wrapper dd.accordion-content")
    dishes = []
    start_date_header = soup.select_one("section#section-1 div.sectionheader div.sectionheader-content h2")
    if not start_date_header:
        raise RuntimeError("Can't find date for the weekly menu; refusing to guess")
    start_date_text = start_date_header.get_text().strip()
    start_date = parser.parse(" ".join(start_date_text.split()[-2:]))
    if start_date.weekday() != 0:
        raise RuntimeError(f"Queen's: week start {start_date:%A %d %B} isn't a Monday, refusing to guess")
    for day_content in day_contents:
        dishes.extend(parse_day(day_content, college, start_date))
    if len(dishes) == 0:
        raise RuntimeError("no data for Queen's")
    return dishes


def parse_day(day_content: bs4.Tag, college: str, start_date: datetime):
    dishes = []
    meal_headers = day_content.select("p strong")
    date = None
    for meal_header in meal_headers:
        try:
            weekday, meal_type = meal_header.get_text().strip().split()
            date = start_date + timedelta(days=weekday_map[weekday.lower()])
        except (ValueError, KeyError):
            LOGGER.warning("meal header format not recognized, skipping meal")
            continue
        if meal_type.lower() not in MEAL_MARKERS:
            LOGGER.warning(f"Unrecognized meal_type {meal_type} on {date}")
            continue
        if normalize_string_data(meal_type) == "brunch":
            dishes.append(Dish(
                name="Brunch menu as usual",
                date=date_isoformat(date),
                course="brunch items",
                college=college,
                meal_type="brunch"
            ))
            continue
        next_el = meal_header.parent.find_next_sibling() # type: ignore
        course_list = next_el if next_el is not None and next_el.name == "ul" else None
        if not course_list:
            LOGGER.warning(f"nothing on {weekday} for {meal_type}")
            continue
        for item in course_list.find_all("li"):
            text = item.get_text(strip=True)
            if text:
                dishes.append(Dish(
                    name=item.get_text(),
                    date=date_isoformat(date),
                    course=None,
                    college=college,
                    meal_type=normalize_string_data(meal_type)
                ))
    if not dishes:
        date_message = f" on {date}" if date else ""
        LOGGER.warning(f"missing day data{date_message}")
    return dishes

if __name__ == "__main__":
    dishes = scrape_queens()
    dishes_sample_printer(dishes)