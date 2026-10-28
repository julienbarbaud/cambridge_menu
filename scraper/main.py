import pymongo as pmg
from pymongo.errors import PyMongoError
from dataclasses import asdict

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from datetime import datetime
from util import DB_URL
from stjohn_scraper import scrape_stjohn
from wolfson_scraper import scrape_wolfson
from trinity_scraper import scrape_trinity
from jesus_scraper import scrape_jesus
from robinson_scraper import scrape_robinson
from selwyn_scraper import scrape_selwyn


SCRAPERS = {
    "St John": scrape_stjohn, 
    "Wolfson": scrape_wolfson, 
    "Trinity": scrape_trinity,
    "Jesus": scrape_jesus,
    "Robinson": scrape_robinson,
    "Selwyn": scrape_selwyn,
}

LOGGER = logging.getLogger(__name__)
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
file_handler = RotatingFileHandler(LOG_DIR / "scrape.log", maxBytes=1_000_000, backupCount=3)
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s %(levelname)s %(name)s %(message)s ",
                    handlers=[logging.StreamHandler(), file_handler]
)


def update_college_db_menu(session, collection, college: str, dates, scraped_dishes):
    session.start_transaction()
    try:
        collection.delete_many({
            "college": college,
            "date": {"$in": dates}
        })
        collection.insert_many([asdict(dish)for dish in scraped_dishes])
    except Exception as e:
        session.abort_transaction()
        raise
    session.commit_transaction()
    

def main():
    LOGGER.info("-"*50)
    LOGGER.info(f"{datetime.now()}")
    LOGGER.info("Starting colleges scraping")
    failed = []

    with pmg.MongoClient(DB_URL) as client:
        db = client.get_database("cambridge_menu")
        dishes_collection = db.get_collection("dishes")
        dishes_collection.create_index([("college", 1), ("date", 1)])
        for college, scraper in SCRAPERS.items():
            try:
                scraped_dishes = scraper(college)
                LOGGER.info(f"{college}: Scraped {len(scraped_dishes)} dishes")
            except Exception as e:
                LOGGER.exception(f"exception during {college} scraping")
                failed.append(college)
                continue
            dates = sorted({dish.date for dish in scraped_dishes})
            with client.start_session().bind() as session:
                try:
                    update_college_db_menu(session, dishes_collection, college, dates, scraped_dishes)
                except Exception as e:
                    failed.append(college)
                    LOGGER.exception(f"error while updating {college} data in db")

    if failed:
        LOGGER.error(f"Failed on {failed}")
        sys.exit(1)                
    LOGGER.info("Done.\n\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        LOGGER.exception(f"Fatal error")
        sys.exit(1)