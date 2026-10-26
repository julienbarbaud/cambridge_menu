import bs4
import logging
from dateutil import parser
from model import Dish
from util import fetch_html, normalize_string_data
from datetime import date

LOGGER = logging.getLogger(__name__)

def scrape_stjohn(college_name: str):
    url = "https://menu.joh.cam/"
    html = fetch_html(url)
    return parse_html(html, college_name)

def parse_html(html, college_name: str):
    soup = bs4.BeautifulSoup(html, "html.parser")
    day_cards = soup.find_all(class_="weekday")
    menu = []
    for day_card in day_cards:
        day_menu = parse_day(day_card, college_name)
        menu.extend(day_menu)
    if not menu:
        raise ValueError("empty menu")
    return menu

def parse_day(day_card: bs4.Tag, college_name: str):
    day_el = day_card.find("h2", class_="text-primary")
    if day_el is None:
        return []
    day_text = day_el.get_text(" ", strip=True)
    try:
        date = parser.parse(day_text).date()
    except ValueError:
        LOGGER.warning(f"Invalid date format: {day_text}")
        return []
    headers = day_card("button", class_="accordion-header")
    dishes = []
    for header in headers:
        header_content = header.find("span")
        if header_content is None:
            continue
        meal_type = header_content.get_text(strip=True)
        meal_content = header.find_next_sibling("div", class_="accordion-content")
        if meal_content is None:
            continue
        meal_dishes = parse_meal(meal_content, meal_type, date, college_name)
        dishes.extend(meal_dishes)
    return dishes
    

def parse_meal(meal_content: bs4.Tag, meal_type: str, date: date, college_name: str):
    dishes = []
    for course_header in meal_content.find_all("h2", class_="border-primary"):
        course_type = course_header.get_text(strip=True)
        item_container = course_header.find_parent()
        if item_container is None:
            continue
        for item in item_container.find_all("p", class_="text-base"):
            dish_name = item.get_text(strip=True)
            dish = Dish(
                course=normalize_string_data(course_type) or None, # if course_type is empty string, set to None
                name=dish_name, 
                meal_type=normalize_string_data(meal_type),  
                date=date.isoformat(), 
                college=college_name
            )
            dishes.append(dish)
    return dishes


if __name__ == "__main__":
    menu = scrape_stjohn("St John")
