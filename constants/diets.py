#constants/diets.py
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SPOONACULAR_API_KEY")

DIETS_CACHE_FILE = os.path.join(os.path.dirname(__file__), "diets_cache.json")
DEFAULT_DIETS = ["vegetarian", "vegan", "gluten free", "ketogenic", "paleo", "pescetarian"]

def fetch_diets_from_api():
    try:
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "apiKey": API_KEY,
            "number": 1  # We don’t need results, just access the diet filters
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            # Spoonacular does not directly return valid diets, so we fallback to known safe list.
            return DEFAULT_DIETS
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch diets: {e}")
    return None

def get_all_diets():
    if os.path.exists(DIETS_CACHE_FILE):
        try:
            with open(DIETS_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass

    diets = fetch_diets_from_api()
    if diets:
        with open(DIETS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(diets, f, indent=2)
        return diets

    return DEFAULT_DIETS

# For convenience in current usage
ALL_DIETS = get_all_diets()
