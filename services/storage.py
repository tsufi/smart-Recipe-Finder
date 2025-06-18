#data/storage.py
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data_files")

HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
FAVORITES_FILE = os.path.join(DATA_DIR, "favorites.json")
MEALPLAN_FILE = os.path.join(DATA_DIR, "mealplan.json")

# Ensure data_files folder exists
os.makedirs(DATA_DIR, exist_ok=True)

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Fix: convert "string" → ["string"]
                if isinstance(default, list) and isinstance(data, str):
                    return [data]
                # Reject wrong types
                if not isinstance(data, type(default)):
                    print(f"[WARNING] Unexpected format in {path}, resetting.")
                    return default
                return data
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON from {path}: {e}")
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_history():
    return load_json(HISTORY_FILE, [])

def save_history(history):
    save_json(HISTORY_FILE, history[:10])  # Limit to last 10 entries

def get_favorites():
    return load_json(FAVORITES_FILE, [])

def save_favorites(favorites):
    save_json(FAVORITES_FILE, favorites)

def get_mealplan():
    return load_json(MEALPLAN_FILE, [])

def save_mealplan(mealplan):
    save_json(MEALPLAN_FILE, mealplan)
