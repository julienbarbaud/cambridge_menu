import bs4
import logging
from util import date_isoformat, fetch_html, dishes_sample_printer, normalize_string_data, MEAL_MARKERS, WEEKDAY_MAP
from model import Dish
from dateutil import parser
from datetime import datetime, timedelta
import re

LOGGER = logging.getLogger()
BASE_URL = "https://www.darwin.cam.ac.uk/dine/weekly-menu/"


def extract_tabs_dates(tabs: list[bs4.Tag]):
    date_tabs = [tab.get_text(strip=True) for tab in tabs]
    prev_date= None
    dates = []
    for date_tab in date_tabs[-1::-1]:
        date_match = re.search(r"w/c\s*([0-9]+(th|rd|nd|st)\s+[A-Za-z]{3})", date_tab)
        if date_match is None:
            if prev_date is None:
                raise RuntimeError("Can not check dates for menu, refusing to guess")
            prev_date = prev_date - timedelta(days=7)
            dates.append(prev_date)
        else:
            prev_date = parser.parse(date_match.group(1))
            dates.append(prev_date)
    dates.reverse()
    return dates
        

def scrape_darwin(college: str="Darwin"):
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    tabs_links = soup.select("ul.menus-tabs a.menus-tab")
    start_dates = extract_tabs_dates(tabs_links)
    week_menus = soup.select("div.menus-content")
    dishes = []
    for week_menu, start_date in zip(week_menus, start_dates):
        for day_title in week_menu.find_all("h3"):
            try:
                weekday = day_title.get_text(strip=True).lower()
                date = start_date + timedelta(days=WEEKDAY_MAP[weekday])
            except:
                LOGGER.warning(f"Can not read weekday on week starting {start_date}; skipping")
                continue
            table = day_title.find_next_sibling()
            while table and table.name == "table":
                header = table.select_one("thead th")
                meal_type = normalize_string_data(header.get_text(strip=True)) if header is not None else None
                if meal_type is None or meal_type not in MEAL_MARKERS:
                    LOGGER.warning(f"Can not read meal_type on {date}; skipping")
                    table = table.find_next_sibling()
                    continue
                rows = table.select("tbody tr")
                for row in rows:
                    meal_cell = row.find_next("td")
                    if not meal_cell:
                        LOGGER.warning(f"skipping malformed meal on {date} {meal_type}")
                        continue
                    dishes.append(Dish(
                        name=meal_cell.get_text(strip=True),
                        course = None,
                        college=college,
                        meal_type=meal_type,
                        date=date_isoformat(date)
                    ))
                table = table.find_next_sibling()
            
    if len(dishes) == 0:
        raise RuntimeError("no data for Darwin")
    return dishes

if __name__ == "__main__":
    dishes = scrape_darwin()
    dishes_sample_printer(dishes)