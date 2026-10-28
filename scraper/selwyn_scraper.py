import bs4
import logging
from datetime import datetime, timedelta
from util import date_isoformat, fetch_html, dishes_sample_printer, normalize_string_data, MEAL_MARKERS
from model import Dish
import time

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.sel.cam.ac.uk/current-members/hall-menu"
MAX_DAYS=31
MAX_MISSES = 3

def scrape_selwyn(college: str="Selwyn"):
    today = datetime.now()
    dishes = []
    consecutive_misses = 0
    for days_passed in range(MAX_DAYS):
        # letting the server breathe
        time.sleep(0.5)
        day = today + timedelta(days=days_passed)
        isodate = date_isoformat(day)
        try:
            url = f"{BASE_URL}?menu_date={isodate}"
            html = fetch_html(url)
        except Exception:
            LOGGER.exception(f"Failed to fetch {url}")
            consecutive_misses += 1
            if consecutive_misses >= MAX_MISSES: 
                break
            continue
        soup = bs4.BeautifulSoup(html, "html.parser")

        new_dishes = parse_day(soup, isodate, college)
        if not new_dishes:
            consecutive_misses += 1
            if consecutive_misses >= MAX_MISSES: 
                break
            continue
        else:
            consecutive_misses = 0
            dishes.extend(new_dishes)
    if len(dishes) == 0:
        raise ValueError(f"no dishes found for {college}")
    return dishes


def parse_day(soup:bs4.BeautifulSoup, isodate: str, college: str):
    menus_container = soup.find("div", class_="hallmenuall")
    if menus_container is None: 
        LOGGER.warning(f"could not find {college} menus on {isodate}")
        return None
    if "no menus" in menus_container.get_text().lower(): return None
    menus = menus_container.find_all("div", class_="hallmenu")
    if len(menus) == 0:
        LOGGER.warning(f"could not find {college} menus on {isodate}")
        return None
    dishes = []
    for menu in menus:
        meal_type_element = menu.find("div", class_="submenuhdr")
        if meal_type_element is None:
            LOGGER.warning(f"missing meal type for {college} on {isodate}")
            continue
        meal_type = normalize_string_data(meal_type_element.get_text(strip=True))
        if meal_type not in MEAL_MARKERS:
            LOGGER.warning(f"unknown meal type {meal_type} for {college} on {isodate}")
            continue
        names = [
            " ".join(s.split())
            for s in menu.find_all(string=True, recursive=False)
            if len(s.strip()) > 0
        ]
        # there is no indication of course type on this website
        new_dishes = [
            Dish(
                name=name,
                course=None,
                meal_type=meal_type,
                date=isodate,
                college=college
            )
            for name in names
        ]
        dishes.extend(new_dishes)
    return dishes


if __name__ == "__main__":
    dishes = scrape_selwyn()
    dishes_sample_printer(dishes)