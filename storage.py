import json
from json.decoder import JSONDecodeError

def load_user_data():
    try:
        with open("user_data.json", "r", encoding="utf-8") as f:
            user_data = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        user_data = {}
    return user_data
