import bs4
import logging
from datetime import datetime, timedelta
from util import date_isoformat, fetch_html, dishes_sample_printer, normalize_string_data
from model import Dish

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://www.corpus.cam.ac.uk/foodmenu/menu/?reference=1"
MEAL_TYPES = {"lunch": 1, "dinner": 2}
SCRAPE_DAYS_AHEAD = 21

def scrape_corpus_christi(college="Corpus Christi"):
    today = datetime.now()
    dishes = []
    for day_offset in range(SCRAPE_DAYS_AHEAD):
        day = today + timedelta(days=day_offset)
        isodate = date_isoformat(day)
        day_url = f"{BASE_URL}&date={isodate}"
        html = fetch_html(day_url)
        soup = bs4.BeautifulSoup(html, "html.parser")
        container = soup.select_one("div#accordionGroup")
        if container is None:
            LOGGER.warning(f"no data found on {isodate}")
            continue
        meal_titles = [normalize_string_data(span.get_text(strip=True)) for span in soup.select("h3 span.accordion-title")]
        meal_tables = soup.select("div.accordion-panel table tbody")
        for meal_type, table in zip(meal_titles, meal_tables):
            new_dishes = parse_meal(meal_type, table, isodate, college)
            dishes.extend(new_dishes)
    if not dishes:
        raise RuntimeError("No data for Corpus Christi")
    return dishes
    

def parse_meal(meal_type: str, table: bs4.Tag, isodate, college):
    cur_course = None
    dishes = []
    for row in table.find_all("tr"):
        potential_course_info = row.find("h3")
        if potential_course_info:
            cur_course = potential_course_info.get_text(strip=True)
        else:
            para = row.select_one("td p")
            if not para:
                continue
            dishes.append(Dish(
                name = para.get_text(strip=True),
                meal_type=meal_type,
                course=cur_course,
                date=isodate,
                college=college
            ))
    if not dishes:
        LOGGER.warning(f"no meal for {meal_type} on {isodate}")
    return dishes


if __name__ == "__main__":
    dishes = scrape_corpus_christi()
    dishes_sample_printer(dishes)