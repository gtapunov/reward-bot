import json
import os
from json.decoder import JSONDecodeError

# Путь к файлу в persistent диске
DATA_PATH = "/data/user_data.json"

def load_user_data():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            user_data = json.load(f)
            print("Содержимое JSON:", user_data)  # для отладки
    except (FileNotFoundError, JSONDecodeError):
        user_data = {}
    return user_data

def save_user_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
