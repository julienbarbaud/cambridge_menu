import bs4
import logging
from util import date_isoformat, fetch_html, dishes_sample_printer, normalize_string_data, MEAL_MARKERS, WEEKDAY_MAP
from model import Dish
from dateutil import parser
from datetime import datetime, timedelta
import re

LOGGER = logging.getLogger()
BASE_URL = "https://viewthe.menu/lyzv"


def extract_tabs_dates(tab_links: list[bs4.Tag]):
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
            prev_date = parser.parse(date_match.group(1))
            dates[prev_date] = link.attrs["href"]
    return dates
        

def scrape_magdalene(college: str="Magdalene"):
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    tabs_links = soup.select("div.k10-menu-selector__options div.k10-menu-selector__option a.k10-menu-selector__option-name")
    start_dates = extract_tabs_dates(tabs_links)
    print(start_dates)
    dishes = []


if __name__ == "__main__":
    scrape_magdalene()