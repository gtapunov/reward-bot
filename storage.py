import json

def load_user_data():
    try:
        with open("user_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
