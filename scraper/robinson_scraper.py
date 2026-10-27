import bs4
import logging
from datetime import datetime, timedelta
from util import date_isoformat, fetch_html, MEAL_MARKERS, dishes_sample_printer, normalize_string_data
from model import Dish
from dateutil import parser

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.robinson.cam.ac.uk/college-life/garden-restaurant-menu"
MAX_DAYS=31

def scrape_robinson(college: str="Robinson"):
    day = datetime.now()
    menu_not_found = False
    dishes = []
    days_passed = 0
    while not menu_not_found and days_passed < MAX_DAYS:   
        isodate = date_isoformat(day)
        # the guys who made the website somehow got the url date wrong with an off-by-one error;
        # querying 2026-10-26 actually serves the page for 10-27 (which actually breaks their UI nav)...
        # have to adapt to that but the solution is probably very fragile depending on the
        # nature of the mistake they made and whether they intend on fixing it
        wrong_fucking_isodate = date_isoformat(day - timedelta(days=1))
        html = fetch_html(f"{BASE_URL}?date={wrong_fucking_isodate}")
        soup = bs4.BeautifulSoup(html, "html.parser")

        new_dishes = parse_day(soup, isodate, college)
        if len(new_dishes) == 0:
            menu_not_found = True
            break
        dishes.extend(new_dishes)
        day = day + timedelta(days=1)
        days_passed += 1
    if len(dishes) == 0:
        raise ValueError(f"no dishes found for Robinson")
    return dishes

# function to double check that the date is correct since the website is broken
def date_matches(isodate: str, soup: bs4.BeautifulSoup):
    date_container = soup.select_one("div.field--name-body h3")
    if date_container is None:
        raise RuntimeError("Robinson college dates not found; can't guarantee data integrity")
    text = date_container.get_text()
    pre_date_text = "Menus for "
    date_text = text[len(pre_date_text)-1:]
    date = parser.parse(date_text)
    if not (date_isoformat(date) == isodate):
        raise RuntimeError("Robinson college dates don't match")





def parse_day(soup: bs4.BeautifulSoup, isodate: str, college: str):
    menus = soup.find_all("div", class_="menuColumn")
    dishes = []
    for menu in menus:
        meal_header = menu.find("h3", recursive=False)

        # the following silently ignores the "snack bar" cards which have been horribly integrated in separate columns
        # it is not clear visually if they belong to both lunch or dinner or just one of them
        if meal_header is None:
            continue

        header_text = meal_header.get_text().lower()
        meal_type = None
        for meal_marker in MEAL_MARKERS:
            if meal_marker in header_text:
                meal_type = meal_marker
                break
        if meal_type is None:
            LOGGER.warning(f"could not read meal type on {isodate} for Robinson")
            continue
        menu_content = menu.find("div", class_="menuItem")
        if menu_content is None:
            LOGGER.warning(f"could not read meal content on {isodate} for Robinson")
            continue
        new_dishes = parse_menu_item(menu_content, meal_type, isodate, college)
        dishes.extend(new_dishes)
    return dishes

def parse_menu_item(item: bs4.Tag, meal_type: str, isodate: str, college: str):
    dishes = []
    strong = item.find("strong")
    course = strong.get_text(strip=True) if strong else None
    names = [
        " ".join(s.split())
        for s in item.find_all(string=True, recursive=False)
        if not isinstance(s, bs4.Comment) and s.strip()
    ]
    for name in names:
        dishes.append(Dish(
            course=normalize_string_data(course) if course is not None else None,
            name=name,
            meal_type=normalize_string_data(meal_type),
            date=isodate,
            college=college
        ))
    return dishes

if __name__ == "__main__":
    dishes = scrape_robinson()
    dishes_sample_printer(dishes)


