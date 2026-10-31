import bs4
import logging
from util import fetch_html, MEAL_MARKERS, dishes_sample_printer, normalize_string_data
from model import Dish

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://newn.cam.ac.uk/weekly-menus"

def scrape_newnham(college: str="Newnham"):
    dishes = []
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    for container in soup.find_all("div", class_="menu-week-container"):
        meal_type_element = container.select_one("div.menu-week-header h1")
        if meal_type_element is None:
            continue
        meal_type = None
        found_markers = 0
        for meal_marker in MEAL_MARKERS:
            if meal_marker in meal_type_element.get_text().lower():
                meal_type = meal_marker
                found_markers += 1
        if found_markers != 1 or meal_type is None:
            LOGGER.warning(f"Can't figure out meal type from {meal_type_element.get_text()}")
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
        LOGGER.warning("skipping day cause date not found")
        return []
    try:
        date = str(day_element.attrs["datetime"]).split("T")[0]
    except KeyError:
        LOGGER.warning(f"missing date")
        return []
    for dish_name_p in day_menu.select("div p"):
        dish_name = dish_name_p.get_text().strip()
        if not dish_name:
            continue
        dishes.append(Dish(
            name=dish_name,
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
