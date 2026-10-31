import bs4
import logging
from util import date_isoformat, fetch_html, dishes_sample_printer, normalize_string_data
from model import Dish
from dateutil import parser

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.chu.cam.ac.uk/about/campus/dining-at-college/lunch-and-dinner-menu/"

def scrape_churchill(college: str="Churchill"):
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    meal_tables = soup.select("figure.wp-block-table table") # no specific class name or id
    dishes = []
    for meal_table in meal_tables:
        dishes.extend(parse_day(meal_table, college))
    if len(dishes) == 0:
        raise RuntimeError("no data for Churchill")
    return dishes


def parse_day(meal_table: bs4.Tag, college: str):
    day_dishes = []
    try:
        header, content = meal_table.find_all("tr") # only two rows
        day_header_cell, lunch_header_cell, dinner_header_cell = header.find_all("td")
        _, lunch_menu_cell, dinner_menu_cell = content.find_all("td")
        assert lunch_header_cell.get_text(strip=True).lower() == "lunch", "Lunch header not in the expected location"
        assert dinner_header_cell.get_text(strip=True).lower() == "dinner", "Dinner header not in the expected location"
        date = parser.parse(day_header_cell.get_text())
    except Exception:
        LOGGER.exception(f"could not read menu_table")
        return []

    data = {"lunch": lunch_menu_cell, "dinner": dinner_menu_cell}
    dishes = {}
    for meal_type in data.keys():
        dishes[meal_type] = [item.strip() for item in data[meal_type].get_text().split('*') if item.strip()]
        if len(dishes[meal_type]) == 1 and dishes[meal_type][0].lower() == "brunch":
            recorded_meal_type = "brunch"
        else:
            recorded_meal_type = meal_type
        for dish in dishes[meal_type]:
            day_dishes.append(Dish(
                name=dish,
                meal_type=normalize_string_data(recorded_meal_type),
                course=None,
                college=college,
                date=date_isoformat(date)
            ))
    if len(day_dishes) == 0:
        LOGGER.warning(f"no data on {date_isoformat(date)}")
    return day_dishes


if __name__=="__main__":
    logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s %(levelname)s %(name)s %(message)s ",
                    handlers=[logging.StreamHandler()]
    )
    dishes = scrape_churchill()
    dishes_sample_printer(dishes)


