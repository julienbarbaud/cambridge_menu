import requests as req
from requests.adapters import HTTPAdapter
import os
import dotenv
from datetime import datetime
from dateutil import parser
from urllib.parse import urlparse

dotenv.load_dotenv()
DB_URL = os.getenv("MONGODB_URI")
if not DB_URL:
    raise RuntimeError("MONGODB_URI is not set (put it in .env locally, or in a GitHub secret)")

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}
MEAL_MARKERS = {"lunch", "dinner", "brunch", "breakfast"}

_sessions = {}

def get_session(domain: str) -> req.Session:
    if domain not in _sessions:
        session = req.Session()
        session.mount("https://", HTTPAdapter(max_retries=3))
        _sessions[domain] = session
    return _sessions[domain]


def fetch_html(url: str):
    session = get_session(urlparse(url).netloc)
    resp = session.get(url, headers={"User-Agent": "colleges-menu-scraper"}, timeout=10)
    resp.raise_for_status()
    return resp.content

def normalize_string_data(data: str):
    case_insensitive = data.lower().strip()
    if case_insensitive in ["side", "sides", "side dish", "side dishes"]:
        case_insensitive = "sides"
    return case_insensitive


def date_isoformat(date: datetime):
    return date.isoformat().split("T")[0]

def get_week_day(isodate: str):
    return parser.parse(isodate).weekday()

def dishes_sample_printer(dishes):
    print(f"found {len(dishes)} dishes")
    print(f"10 first:")
    try:
        for i in range(10):
            print(dishes[i])
        print("10 last:")
        for i in range(10):
            print(dishes[-10+i])
    except IndexError:
        print("there is less than 10 items, probably abnormal")