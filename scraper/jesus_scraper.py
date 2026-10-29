import bs4
import logging
from datetime import datetime, timedelta
from util import date_isoformat, fetch_html, dishes_sample_printer, normalize_string_data
from model import Dish


LOGGER = logging.getLogger(__name__)
BASE_URL = "https://apps.jesus.cam.ac.uk/foodmenuview/digiboard.php"
MEAL_TYPES = {"lunch": 1, "dinner": 2}
SCRAPE_DAYS_AHEAD = 21

def scrape_jesus(college: str):
    lunches = scrape_meal_type("lunch", college)
    dinners = scrape_meal_type("dinner", college)
    dishes = lunches + dinners
    if not dishes:
        raise ValueError(f"{college} college has an empty menu") 
    return dishes 

def scrape_meal_type(meal_type: str="lunch", college: str="Jesus"):
    now = datetime.now()
    dishes = []
    for day_shift in range(SCRAPE_DAYS_AHEAD):
        day = now + timedelta(days=day_shift)
        isoday = date_isoformat(day)
        url = f"{BASE_URL}?event_id={MEAL_TYPES[meal_type]}&date={isoday}"
        try:
            html = fetch_html(url)
        except Exception:
            LOGGER.exception(f"could not fetch {url}")
            continue
        soup = bs4.BeautifulSoup(html, "html.parser")
        new_dishes = parse_meal(soup, meal_type, isoday, college)
        if not new_dishes:
            LOGGER.warning(f"No dishes found for {meal_type} on {isoday}")
        dishes.extend(new_dishes)
    return dishes

def parse_meal(soup: bs4.BeautifulSoup, meal_type: str, isoday: str, college: str):
    menu = soup.find("table", class_="fm-menu-courses")
    if menu is None:
        return []
    rows = menu.find_all("tr")
    cur_course = None
    dishes = []
    for row in rows:
        h4_match, fm_item_match = row.find("h4"), row.find("td", class_="fm-item-label")
        if h4_match is not None:
            cur_course = h4_match.get_text()
        elif fm_item_match is not None:
            dishes.append(Dish(
                course = normalize_string_data(cur_course) if cur_course is not None else None,
                name=fm_item_match.get_text(),
                meal_type=meal_type,
                date=isoday,
                college=college
            ))
    return dishes


if __name__ == "__main__":
    dishes = scrape_jesus("Jesus")
    dishes_sample_printer(dishes)