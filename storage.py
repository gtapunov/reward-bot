import json

def load_user_data():
    try:
        with open("user_data.json", "r", encoding="utf-8") as f:
            user_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}
