import requests as req
import os
import dotenv

# ENV_FILE = "/Users/julienmeow/Developer/VS_Projects/colleges_menu/.env"
# if not os.path.isfile(ENV_FILE):
#     raise FileNotFoundError(".env file containing authentication information not found; can't connect to the database")
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
    return data.lower().strip()