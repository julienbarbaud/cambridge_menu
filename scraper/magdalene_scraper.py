import bs4
import logging
from util import date_isoformat, fetch_html, dishes_sample_printer, normalize_string_data, MEAL_MARKERS, WEEKDAY_MAP
from model import Dish
from dateutil import parser
from datetime import datetime, timedelta
import re
from playwright.sync_api import sync_playwright

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://viewthe.menu/lyzv"
MAX_DAYS_PAST = 14

def scrape_magdalene(college: str="Magdalene"):
    html = playwright_html_load()
    soup = bs4.BeautifulSoup(html, "html.parser")
    tabs_links = soup.select("div.k10-menu-selector__options div.k10-menu-selector__option a.k10-menu-selector__option-name")
    start_dates = extract_tabs_dates(tabs_links)
    dishes = []
    for start_date, url in start_dates.items():
        new_dishes = parse_week(start_date, url, college)
        dishes.extend(new_dishes)
    if not dishes:
        raise RuntimeError(f"No data for {college}")
    return dishes

def is_hidden_upward(tag):
    for parent in tag.parents:
        if hasattr(parent, 'get'):
            style = parent.get('style', '')
            if 'display:none' in style.lower().replace(' ', ''):
                return True
    return False

def parse_week(start_date, url, college):
    dishes = []
    html = playwright_html_load(url)
    soup = bs4.BeautifulSoup(html, "html.parser")
    day_menus = soup.select("div.k10-course_level_1")
    # print(f"menus on week com {start_date}: {len(day_menus)}")
    skip=0
    for day_menu in day_menus:
        if not is_hidden_upward(day_menu):
            skip+=1
            dishes.extend(parse_day(start_date, day_menu, college))
    # print(f"skipped {skip} menus on wek com {start_date}")
    return dishes


def parse_day(monday_date, day_menu: bs4.Tag, college):
    dishes = []
    day_header = day_menu.select_one("div.k10-course__header_level_1 div.k10-course__name-text")
    if not day_header:
        LOGGER.warning("Can not read week day; skipping data")
        return []
    week_day = day_header.get_text(strip=True).lower()
    try:
        date = monday_date + timedelta(days=WEEKDAY_MAP[week_day])
    except KeyError:
        # Their website is a mess and they somehow sometimes (often) screw up the formatting
        #  writing the "dinner" subheader in a level 1 header supposed to contain day...
        # That means that they separate lunch and dinner in two different day cards 
        # I want no part of this, so we catch the KeyError and just give up on the data altogether
        LOGGER.warning(f"Can't recognize {week_day} as a week day; skipping data")
        return []
    isodate = date_isoformat(date)
    meal_type_headers = day_menu.select("div.k10-course__header_level_2 div.k10-course__name-text")
    meal_types = [header.get_text(strip=True).lower() for header in meal_type_headers]
    courses_containers = [container for container in day_menu.select("div.k10-course__body div.k10-grid_columns_2") if container.select_one("div.k10-recipe__body")]
    if not len(meal_types) == len(courses_containers):
        LOGGER.warning(f"meal type headers ({len(meal_types)}) don't match the number of meal sections ({len(courses_containers)})")
        return []

    for meal_type, courses_container in zip(meal_types, courses_containers):
        if any(marker in meal_type for marker in ["brunch", "breakfast"]):
            meal_type = "brunch"
        elif any(marker in meal_type for marker in ["dinner", "night"]):
            meal_type = "dinner"
        elif any(marker in meal_type for marker in ["lunch", "day"]):
            meal_type = "lunch"
        else:
            LOGGER.warning(f"unrecognized meal type {meal_type}; skipping")
            continue
        for course_span in courses_container.select("div.k10-recipe__body span.k10-recipe__name"):
            dishes.append(Dish(
                name = course_span.get_text(strip=True),
                meal_type=meal_type,
                college=college,
                date=isodate,
                course=None
            ))
    return dishes





def extract_tabs_dates(tab_links: list[bs4.Tag]):
    now = datetime.now()
    date_spans = [tab.find("span", class_="k10-menu-selector__option-name-wrapper") for tab in tab_links]
    date_strings = [span.get_text(strip=True).lower() for span in date_spans if span]
    dates = {}
    for date_string, link in zip(date_strings, tab_links):
        if "ramsay" not in date_string:
            continue
        date_match = re.search(r"ramsay\s*wk.*com\s*([0-9]+/[0-9]+/[0-9]+)", date_string)
        if date_match is None:
            raise RuntimeError("Can not check dates for menu, refusing to guess")
        else:
            prev_date = None
            for format_string in ["%d/%m/%Y", "%d/%m/%y"]:
                # they, annoyingly enough, use inconsistent formatting between 2 and 4-digit year
                # so we try both and pray they dont come up with another one (they will)
                try:
                    prev_date = datetime.strptime(date_match.group(1), format_string)
                    break
                except ValueError:
                    pass
            if not prev_date:
                LOGGER.warning("Could not read week starting date; skipping")
                continue

            if (now - prev_date) <= timedelta(days=MAX_DAYS_PAST):
                dates[prev_date] = link.attrs["href"]
    return dates
        

def playwright_html_load(url=BASE_URL):
    # this is needed because the menu page is rendered dynamically with js
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html_content = page.content()
        browser.close()
        return html_content
    


if __name__ == "__main__":
    dishes = scrape_magdalene()
    dishes_sample_printer(dishes)