import bs4
import logging
from datetime import datetime, timedelta
from util import date_isoformat, fetch_html, playwright_html_load, MEAL_MARKERS, dishes_sample_printer, normalize_string_data
from model import Dish
import re
import soupsieve
from dateutil import parser

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.clarehall.cam.ac.uk/dining/"


def get_menu_url() -> str:
    soup = bs4.BeautifulSoup(fetch_html(BASE_URL), "html.parser")
    menu_url = None
    for header_link in soup.select("#main article.wrapper div.wp-block-buttons div.wp-block-button a"):
        if re.search("view.*menu", header_link.get_text(strip=True), re.IGNORECASE):
            menu_url = header_link.get('href')
            if menu_url:
                break
    if menu_url is None:
        raise RuntimeError("Could not find a link to the menu")
    return str(menu_url)


def search_between(delimiters: list[bs4.Tag], css_query, end_element = None):
    delimiter_matches_map = {}
    for i, delimiter in enumerate(delimiters):
        stop_element = delimiters[i+1] if i+1 < len(delimiters) else end_element
        stop_elements = set([stop_element, *stop_element.parents]) if stop_element else set()
        matches = []
        for element in delimiter.find_all_next():
            if element in stop_elements:
                break
            if soupsieve.match(css_query, element):
                matches.append(element)
        delimiter_matches_map[delimiter] = matches
    return delimiter_matches_map


def scrape_clare_hall(college="Clare Hall"):
    menu_url = get_menu_url()
    soup = bs4.BeautifulSoup(playwright_html_load(menu_url), "html.parser")
    day_headers = soup.select("div.ChapterTitleNone span")
    days2meal_sections = search_between(day_headers, "div.container div.text_wrapper")
    dishes = []
    for day_header, meal_sections in days2meal_sections.items():
        try:
            date = date_isoformat(parser.parse(day_header.get_text(strip=True).lower()))
        except parser.ParserError:
            LOGGER.warning(f"Could not parse the date {day_header.get_text(strip=True)},skipping day")
            continue
        for meal_section in meal_sections:
            new_dishes = parse_meal(meal_section, date, college)
            dishes.extend(new_dishes)
        
    if not dishes:
        raise RuntimeError(f"No dishes for {college}")
    return dishes

def parse_meal(meal_section: bs4.Tag, isodate: str, college: str):
    meal_type_header = meal_section.select_one("p span.TextBodyEmph")
    dishes = []
    if not meal_type_header:
        LOGGER.warning(f"can not find meal type for one of the sections on {isodate}, skipping")
        return []
    meal_type = meal_type_header.get_text(strip=True).lower()
    if meal_type not in MEAL_MARKERS:
        LOGGER.warning(f"unknown meal type {meal_type} on {isodate}, skipping")
        return []
    for meal_item in meal_section.select("p span"):
        if meal_item == meal_type_header or "TextBodyEmph" in str(meal_item.get('class')):
            continue
        dishes.append(Dish(
            name=meal_item.get_text(strip=True),
            meal_type=normalize_string_data(meal_type),
            college=college,
            date=isodate,
            course=None
        ))
    if not dishes:
        LOGGER.warning(f"empty meal section for {meal_type} on {isodate}")
    return dishes



if __name__ == "__main__":
    dishes = scrape_clare_hall()
    dishes_sample_printer(dishes)