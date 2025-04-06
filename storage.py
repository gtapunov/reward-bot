import json
from json.decoder import JSONDecodeError

def load_user_data():
    try:
        with open("user_data.json", "r", encoding="utf-8") as f:
            user_data = json.load(f)
            print("Содержимое JSON:", f.read())  # временно, чтобы отладить
    except (FileNotFoundError, JSONDecodeError):
        user_data = {}
    return user_data
