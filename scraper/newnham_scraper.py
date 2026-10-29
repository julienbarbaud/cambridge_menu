import bs4
import logging
from datetime import datetime
from util import fetch_html, MEAL_MARKERS, dishes_sample_printer, normalize_string_data
from model import Dish

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://newn.cam.ac.uk/weekly-menus"

def scrape_newnham(college: str="Newnham"):
    day = datetime.now()
    dishes = []
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    print("souped up")
    for container in soup.find_all("div", class_="menu-week-container"):
        print("in container")
        # if container is None:
        #     continue
        meal_type_element = container.select_one("div.menu-week-header h1")
        if meal_type_element is None:
            continue
        meal_type = None
        for meal_marker in MEAL_MARKERS:
            if meal_marker in meal_type_element.get_text().lower():
                meal_type = meal_marker
        if meal_type is None:
            continue

        for day_menu in container.select("div.paragraph--type--day-menu"):
            new_dishes = parse_day_meal(meal_type, day_menu, college)
            # on saturdays, there seems to be only one "lunch" item named "brunch"
            # handling proper categorization of this case:
            if len(new_dishes) == 1 and new_dishes[0].name.lower() == "brunch":
                new_dishes[0].meal_type = "brunch"
            dishes.extend(new_dishes)
    if not dishes:
        raise RuntimeError(f"no data for {college}")
    return dishes


def parse_day_meal(meal_type: str, day_menu: bs4.Tag, college):
    dishes = []
    day_element = day_menu.find("time")
    if day_element is None:
        LOGGER.warning("skipping day cause date not fond")
        return []
    date = str(day_element.attrs["datetime"]).split("T")[0]
    for dish_name in day_menu.select("div p"):
        dishes.append(Dish(
            name=dish_name.get_text(),
            meal_type=normalize_string_data(meal_type),
            date=date,
            course=None,
            college=college
        ))
    if not dishes:
        LOGGER.warning(f"no data on {date}")
    return dishes

if __name__ == "__main__":
    dishes = scrape_newnham()
    dishes_sample_printer(dishes)
