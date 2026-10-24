import pymongo as pmg
from dataclasses import asdict

from util import DB_URL
from model import Dish
from stjohn_scraper import scrape_stjohn
from wolfson_scraper import scrape_wolfson
from trinity_scraper import scrape_trinity


SCRAPERS = {
    "stjohn": scrape_stjohn, 
    "wolfson": scrape_wolfson, 
    "trinity": scrape_trinity
}

def run_scrapers() -> list[Dish]:
    dishes = []
    for scraper in SCRAPERS.values():
        dishes.extend(scraper())
    return dishes

def upload__to_db():
    pass

if __name__ == "__main__":
    scraped_dishes = run_scrapers()
    print(scraped_dishes)
    client = pmg.MongoClient(DB_URL)
    try:
        db = client.get_database("cambridge_menu")
        dishes_collection = db.get_collection("dishes")
        dishes_collection.insert_many([asdict(dish) for dish in scraped_dishes])
    except Exception as e:
        raise(Exception(f"can't read db because of: {e}"))
    finally:
        client.close()