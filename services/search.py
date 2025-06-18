# services/search.py

import os
import random
import requests
from dotenv import load_dotenv

from services.recipes import find_by_ingredients, get_recipe_info, matches_diet

load_dotenv()
API_KEY    = os.getenv("SPOONACULAR_API_KEY")
MEALDB_URL = "https://www.themealdb.com/api/json/v1/1"

def get_random_recipes(number=5):
    """
    Fetch up to `number` random recipes:
      1) from Spoonacular’s /random endpoint
      2) fallback to MealDB’s random.php
    Each result gets a .source field ("spoonacular" or "mealdb").
    """
    results = []

    # 1) Spoonacular random endpoint
    try:
        resp = requests.get(
            "https://api.spoonacular.com/recipes/random",
            params={"apiKey": API_KEY, "number": number},
            timeout=8
        )
        resp.raise_for_status()
        data = resp.json().get("recipes", [])
        for r in data:
            r["source"] = "spoonacular"
        results.extend(data)
    except Exception:
        # ignore and fallback below
        pass

    # 2) Fallback: MealDB
    while len(results) < number:
        try:
            resp = requests.get(f"{MEALDB_URL}/random.php", timeout=5)
            resp.raise_for_status()
            meals = resp.json().get("meals") or []
            if not meals:
                continue
            m = meals[0]
            # normalize minimal fields
            results.append({
                "id":            int(m["idMeal"]),
                "title":         m["strMeal"],
                "image":         m["strMealThumb"],
                "source":        "mealdb"
            })
        except Exception:
            break

    return results[:number]

def matches_diet(recipe, selected_diets):
    if not selected_diets:
        return True

    recipe_diets = recipe.get("diets", [])
    return all(diet.lower() in [d.lower() for d in recipe_diets] for diet in selected_diets)
