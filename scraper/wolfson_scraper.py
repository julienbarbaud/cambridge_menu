import bs4
from dateutil import parser
from model import Dish
from util import fetch_html, normalize_string_data
import logging

LOGGER = logging.getLogger(__name__)


def scrape_wolfson(college_name: str):
    url="https://www.wolfson.cam.ac.uk/food/cafeteria-menus"
    html = fetch_html(url)
    return parse_html(html, college_name)

def parse_html(html, college_name: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    menu_container = soup.find("div", class_="food-menu")
    dishes = []
    if menu_container is None:
        raise ValueError("no Wolfson menu")
    meal_lists = menu_container.find_all("ul", class_="food-menu__list")
    for meal_list in meal_lists:
        day_header = meal_list.find_previous_sibling("h3")
        if day_header is None:
            continue
        dishes.extend(parse_day(day_header, meal_list, college_name))
    if not dishes:
        raise ValueError("empty menu for Wolfson")
    return dishes
    


def parse_day(day_header: bs4.Tag, meal_list: bs4.Tag, college_name: str):
    try:
        date_text = day_header.get_text(" ", strip=True)
        date = parser.parse(date_text).date()
    except ValueError:
        LOGGER.warning(f"can not parse date {date_text}")
        return []
    dishes = []
    for meal_container in meal_list.find_all("li", recursive=False):
        meal_title = meal_container.select_one("a.collapse__top h4")
        if meal_title is None:
            LOGGER.warning("can't read wolfson meal title")
            continue
        meal_type = meal_title.get_text(strip=True)
        for meal_row in meal_container.find_all("div", class_="single-food-menu-item"):
            course_container = meal_row.find("h4")
            if course_container is None:
                continue
            # all h4 containers must contain 2 spans; one for course information (potentially empty) and one for course name
            course_info = course_container.find_all("span")
            if not course_info or len(course_info) != 2:
                LOGGER.warning("Problem with wolfson course formatting")
                continue
            course_type, dish = [info.get_text(strip=True) for info in course_info]
            if not dish:
                continue
            dishes.append(Dish(
                course=normalize_string_data(course_type) or None, # if course_type is empty string, set to None
                name=dish, 
                meal_type=normalize_string_data(meal_type), 
                date=date.isoformat(),
                college=college_name
            ))

    return dishes




if __name__ == "__main__":
    print(scrape_wolfson("Wolfson"))
