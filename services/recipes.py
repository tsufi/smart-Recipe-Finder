import requests
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
API_KEY = os.getenv("SPOONACULAR_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ SPOONACULAR_API_KEY is not set in your .env file.")

# --------------------------
# Parallel search entrypoint
# --------------------------
def find_by_ingredients(ingredients, number=10):
    def fetch_spoonacular():
        try:
            return _spoonacular_search(ingredients, number)
        except Exception as e:
            print("[ERROR] Spoonacular failed:", e)
            return []

    def fetch_themealdb():
        try:
            return fallback_themealdb(",".join(ingredients))
        except Exception as e:
            print("[ERROR] TheMealDB failed:", e)
            return []

    with ThreadPoolExecutor(max_workers=2) as executor:
        spoon_future = executor.submit(fetch_spoonacular)
        mealdb_future = executor.submit(fetch_themealdb)

        spoon_results = spoon_future.result()
        mealdb_results = mealdb_future.result()

    combined = spoon_results + mealdb_results
    return combined[:number]


# --------------------------------
# Spoonacular integration (filters Foodista)
# --------------------------------
def _spoonacular_search(ingredients, number=10):
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "ingredients": ",".join(ingredients),
        "number": number,
        "ranking": 1,
        "ignorePantry": True,
        "apiKey": API_KEY
    }
    r = requests.get(url, params=params, timeout=8)
    if r.status_code != 200:
        print(f"[ERROR] Spoonacular responded with {r.status_code}: {r.text}")
        return []

    raw_results = r.json()
    filtered = []

    # Fetch detailed info for each recipe to get `sourceName`
    for r in raw_results:
        rid = r.get("id")
        if not rid:
            continue

        detail = get_recipe_info(rid)
        if not detail:
            continue

        source_name = (detail.get("sourceName") or "").lower()
        source_url = (detail.get("sourceUrl") or "").lower()

        if "foodista" in source_name or "foodista" in source_url:
            continue  # skip foodista

        detail["source"] = "spoonacular"
        filtered.append(detail)

    return filtered


def get_recipe_info(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {
        "includeNutrition": True,
        "includeIngredients": True,
        "apiKey": API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=8)
        if r.status_code == 200:
            return r.json()
        print(f"[ERROR] Failed to fetch recipe info ({r.status_code}): {r.text}")
    except requests.RequestException as e:
        print(f"[ERROR] Spoonacular recipe info failed: {e}")
    return None


def matches_diet(info, selected):
    tags = {
        "vegetarian": info.get("vegetarian", False),
        "vegan": info.get("vegan", False),
        "gluten free": info.get("glutenFree", False),
        "ketogenic": info.get("ketogenic", False),
        "paleo": "paleolithic" in info.get("diets", []),
        "pescetarian": "pescetarian" in info.get("diets", [])
    }
    return all(tags.get(d, False) for d in selected)


# ------------------------------
# Fallback: TheMealDB (with filters)
# ------------------------------
def fallback_themealdb(query):
    print("[INFO] Using TheMealDB fallback...")
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={query}"
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            print(f"[ERROR] TheMealDB error: {r.status_code}")
            return []

        data = r.json()
        meals = data.get("meals", [])
        filtered = [
            convert_mealdb_recipe(meal)
            for meal in meals
            if meal and _is_valid_mealdb(meal)
        ]
        return filtered

    except Exception as e:
        print("[ERROR] TheMealDB fallback failed:", e)
    return []


def _is_valid_mealdb(meal):
    # Filter out meals with missing fields or junk
    return (
        meal.get("strInstructions") and
        meal.get("strMealThumb") and
        meal.get("strMeal") and
        any(meal.get(f"strIngredient{i}") for i in range(1, 21))
    )


def convert_mealdb_recipe(meal):
    steps = meal.get("strInstructions", "")
    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        if ing and ing.strip():
            ingredients.append({"original": ing.strip()})

    return {
        "id": meal.get("idMeal"),
        "title": meal.get("strMeal", "Untitled"),
        "image": meal.get("strMealThumb"),
        "summary": steps,
        "sourceUrl": meal.get("strSource", ""),
        "readyInMinutes": 30,
        "servings": 1,
        "extendedIngredients": ingredients,
        "analyzedInstructions": [{
            "name": "Steps",
            "steps": [
                {"number": idx + 1, "step": s.strip()}
                for idx, s in enumerate(steps.split(". ")) if s.strip()
            ]
        }],
        "source": "mealdb"
    }
