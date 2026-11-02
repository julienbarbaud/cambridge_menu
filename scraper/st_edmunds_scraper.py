import calendar
import logging
import re
from datetime import date, timedelta
from pdfplumber.utils.text import extract_text
import bs4
from model import Dish
from util import fetch_html, dishes_sample_printer, WEEKDAYS

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://my.st-edmunds.cam.ac.uk/category/menus/"


def get_menu_pdfs() -> dict:
    html = fetch_html(BASE_URL)
    soup = bs4.BeautifulSoup(html, "html.parser")
    week_rows = soup.select("div.main div.container div.row article.card div.row div.entry-content")
    weeks_paragraphs = [row.find("p") for row in week_rows]
    # there is typically two links per week (one for lunch, one for supper)
    links = [row.select("a.pdfemb-viewer") for row in week_rows]
    url_label_map = {}
    for row, lunch_supper_links in zip(weeks_paragraphs, links):
        label = row.get_text(strip=True).lower() if row else ""
        urls = [link.attrs["href"] for link in lunch_supper_links if link and "href" in link.attrs]
        url_label_map[label] = urls
    return url_label_map

if __name__ == "__main__":
    print(get_menu_pdfs())