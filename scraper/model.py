from datetime import datetime
from dataclasses import dataclass

@dataclass
class Dish:
    course: str|None
    name: str
    meal_type: str
    date: str
    college: str

