import requests as req
import os
import dotenv
from datetime import datetime

dotenv.load_dotenv()
DB_URL = os.getenv("MONGODB_URI")
if not DB_URL:
    raise RuntimeError("MONGODB_URI is not set (put it in .env locally, or in a GitHub secret)")

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MEAL_MARKERS = {"lunch", "dinner", "brunch", "breakfast"}

def fetch_html(url: str):
    resp = req.get(url, headers={"User-Agent": "colleges-menu-scraper"}, timeout=10)
    resp.raise_for_status()
    return resp.content

def normalize_string_data(data: str):
    case_insensitive = data.lower().strip()
    if case_insensitive in ["side", "sides", "side dish", "side dishes"]:
        case_insensitive = "sides"
    return case_insensitive


def date_isoformat(date: datetime):
    return date.isoformat().split("T")[0]

def dishes_sample_printer(dishes):
    print(f"found {len(dishes)} dishes")
    print(f"10 first:")
    try:
        for i in range(10):
            print(dishes[i])
        print("10 last:")
        for i in range(10):
            print(dishes[-1-i])
    except IndexError:
        print("there is less than 10 items, probably abnormal")