# planner.py
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from models import db, MealPlan, Recipe
from datetime import datetime, timedelta
import requests
import os


planner_bp = Blueprint('planner', __name__)

def get_recipe_info(recipe_id):
    SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
    if not SPOONACULAR_API_KEY:
        return None

    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeNutrition": False
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None

    data = response.json()

    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "image": data.get("image"),
        "sourceUrl": data.get("sourceUrl"),
        "servings": data.get("servings"),
        "readyInMinutes": data.get("readyInMinutes"),
        "ingredients": "\n".join([i['original'] for i in data.get('extendedIngredients', [])]),
        "instructions": data.get("instructions") or "No instructions provided.",
    }

@planner_bp.route('/planner', methods=['GET', 'POST'])
@login_required
def planner():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]

    if request.method == 'POST':
        date = request.form['date']
        meal_type = request.form['meal_type']
        recipe_id = request.form['recipe_id']
        new_entry = MealPlan(
            user_id=current_user.id,
            date=date,
            meal_type=meal_type,
            recipe_id=recipe_id
        )
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('planner.planner'))

    # Load planned meals for current user & week
    meals = MealPlan.query.filter(
        MealPlan.user_id == current_user.id,
        MealPlan.date >= week_dates[0],
        MealPlan.date <= week_dates[-1]
    ).all()

    # Load user recipes (for dropdowns)
    recipes = Recipe.query.all()

    return render_template("planner.html", week_dates=week_dates, meals=meals, recipes=recipes)

@planner_bp.route('/add-to-meal/<string:source>/<int:recipe_id>', methods=["GET"])
@login_required
def add_external_to_meal(source, recipe_id):
    recipe = get_recipe_info(recipe_id)
    if not recipe:
        return render_template("error.html", message=_("error_default")), 404

    return render_template(
        "planner_add_external.html",
        recipe=recipe,
        source=source,
        recipe_id=recipe_id
    )

@planner_bp.route('/planner/add', methods=['POST'])
@login_required
def add_to_meal_plan():
    date = request.form['date']
    meal_type = request.form['meal_type']
    recipe_id = request.form['recipe_id']

    new_entry = MealPlan(
        user_id=current_user.id,
        date=date,
        meal_type=meal_type,
        recipe_id=recipe_id
    )
    db.session.add(new_entry)
    db.session.commit()
    flash(_("mealplan_saved"), "success")
    return redirect(url_for('planner.planner'))
