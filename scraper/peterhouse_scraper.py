import requests
import logging
from model import Dish
from util import dishes_sample_printer, get_week_day

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://petmenu.co.uk/servery.json"





def scrape_peterhouse(college: str="Peterhouse"):
    try:
        resp = requests.get(BASE_URL)
    except Exception:
        raise RuntimeError(f"Could not connect to {BASE_URL}")

    dishes=[]
    data = resp.json()
    daily_breakfast_items = [item[0] for item in data["breakfast"]]
    for date, meals in data["menus_by_date"].items():
        daily_dishes=[]
        entries = {
            "desserts": {"meal_type": ["lunch", "dinner"], "course": "dessert"},
            "potato": {"meal_type": ["lunch"], "course": "potato"},
            "lunch": {"subcategories": {
                "sides": {"meal_type": ["lunch"], "course": "sides"},
                "mains": {"meal_type": ["lunch"], "course": "mains"}
            }},
            "dinner": {"subcategories": {
                "sides": {"meal_type": ["dinner"], "course": "sides"},
                "mains": {"meal_type": ["dinner"], "course": "mains"}
            }},
            "brunch": {"subcategories": {
                "regular": {"meal_type": ["brunch"], "course": "regulars"},
                "specials": {"meal_type": ["brunch"], "course": "specials"}
            }}
        }

        def add_dish(dish_fields, dish_data):
            if "subcategories" in dish_fields:
                for subkey, subcategory in dish_fields["subcategories"].items():
                    if subkey in dish_data and dish_data[subkey]:
                        add_dish(subcategory, dish_data[subkey])
                return
            
            for meal_type in dish_fields["meal_type"]:
                if meal_type in meals:
                    for dish in dish_data:
                        daily_dishes.append(Dish(
                            name=dish[0],
                            meal_type=meal_type,
                            course=dish_fields["course"],
                            college=college,
                            date=date
                        ))

        for key, item_fields in entries.items():
            if key in meals and meals[key]:
                add_dish(item_fields, meals[key])

        # treating soup as a special case because its structure is different for some reason
        if "soup" in meals and len(meals["soup"])>0 and meals["soup"][0]:
            daily_dishes.append(Dish(
                name=meals["soup"][0],
                meal_type="lunch",
                course="soup",
                college=college,
                date=date
            ))

        if not daily_dishes:
            LOGGER.warning(f"no data on {date} (except for regular breakfast)")

        #treating breakfast apart as well because it's always the same
        if get_week_day(date) not in [5,6]:
            # weekend days have neither lunch nor breakfast; skipping breakfast 
            daily_dishes.extend([
                Dish(
                    name=name, 
                    course="breakfast items",
                    meal_type="breakfast",
                    college=college,
                    date=date
                )
                for name in daily_breakfast_items
            ])
        dishes.extend(daily_dishes)

    if not dishes:
        raise RuntimeError("no data found for Peterhouse")
    return dishes


if __name__ == "__main__":
    dishes = scrape_peterhouse()
    dishes_sample_printer(dishes)