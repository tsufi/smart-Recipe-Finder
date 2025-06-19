import os
from datetime import datetime, timedelta

from flask import (
    Flask, Blueprint, render_template, request,
    redirect, url_for, session, g
)
from services.email_service import send_email
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
from planner import planner_bp  # adjust path as needed
from flask_migrate import Migrate
from flask.cli import with_appcontext
from flask_login import current_user, LoginManager, login_required
from models import log_event
from flask_babel import _
import click


# 1) Load environment vars
load_dotenv()

# 2) Create Flask app
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-prod")

# Debug: Print and echo the database URI
app.config['SQLALCHEMY_ECHO'] = True
print(f"🗄️  DATABASE_URI: {os.getenv('DATABASE_URL')}")

# 3) Configure Mail
app.config.update(
    MAIL_SERVER         = os.getenv("MAIL_SERVER"),         # smtp.mailgun.org
    MAIL_PORT           = int(os.getenv("MAIL_PORT", 587)), # 587 or 465
    MAIL_USE_TLS        = True,
    MAIL_USERNAME       = os.getenv("MAIL_USERNAME"),       # postmaster@yourdomain.com
    MAIL_PASSWORD       = os.getenv("MAIL_PASSWORD"),       # Your Mailgun SMTP password
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")  # Same as MAIL_USERNAME
)

# 4) Configure and initialize the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, SavedRecipe, MealPlan

db.init_app(app)
with app.app_context():
    db.create_all()


# 5) Serializer for password resets
serializer = URLSafeTimedSerializer(app.secret_key)

# 6) Register auth blueprint
from auth import auth_bp
app.register_blueprint(auth_bp)

# 7) Import recipe services
from services.search import (
    get_random_recipes,
    find_by_ingredients,
    get_recipe_info,
    matches_diet
)

app.register_blueprint(planner_bp)
migrate = Migrate(app, db)

from admin import admin_bp
app.register_blueprint(admin_bp)

login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Adjust route name if different
login_manager.init_app(app)  # <-- this is what you're missing

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# —— LANGUAGE SUPPORT —— #

# List of supported languages
LANGUAGES = {
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "fi": "Suomi",
}

# 8) Public endpoint to switch language
@app.route("/set_language/<lang>")
def set_language(lang):
    if lang in LANGUAGES:
        if current_user.is_authenticated:
            current_user.preferred_language = lang
            db.session.commit()
        else:
            session['language'] = lang
    return redirect(request.referrer or url_for('index'))

# 9) Instantiate Translator
from utils.translator import Translator
translator = Translator()  # defaults to ./lang/{code}.json

# 10) Load per-request language
@app.before_request
def apply_language_selection():
    if current_user.is_authenticated:
        g.language = current_user.preferred_language or 'en'
    else:
        g.language = (
            session.get('language') or
            request.accept_languages.best_match(list(LANGUAGES.keys())) or
            'en'
        )
    translator.load_language(g.language)
    
   
def track_page_visit():
    if not request.path.startswith("/static") and request.endpoint != "static":
        user_id = current_user.id if current_user.is_authenticated else None
        log_event("page_visit", user_id=user_id, details=request.path)

# 11) Inject helpers into templates
@app.context_processor
def _inject_globals():
    return {
        "_": translator._,
        "LANGUAGES": LANGUAGES,
        "current_language": getattr(g, "language", "en"),
        "request": request
    }
    
# —— Homepage cache —— #
_cached_recipes = []
_cached_time    = None
CACHE_DURATION  = timedelta(hours=6)

@app.route("/")
def index():
    global _cached_recipes, _cached_time
    now = datetime.utcnow()
    if _cached_time is None or now - _cached_time > CACHE_DURATION:
        _cached_recipes = get_random_recipes(number=8)
        _cached_time    = now
    return render_template("index.html", recipes=_cached_recipes)

@app.route("/search", methods=["GET", "POST"])
def search():
    ingredients = ""
    results = []
    if request.method == "POST":
        ingredients = request.form.get("ingredients", "")
        ing_list = [i.strip() for i in ingredients.split(",") if i.strip()]
        if ing_list:
            results = find_by_ingredients(ing_list, number=20)
    return render_template(
        "search.html",
        ingredients=ingredients,
        results=results
    )


@app.route("/external/<int:recipe_id>")
def view_external(recipe_id):
    info = get_recipe_info(recipe_id)
    if not info:
        return render_template("error.html", message=_("error_default")), 404

    recipe = {
        "title":          info.get("title") or info.get("name", ""),
        "image":          info.get("image", ""),
        "ingredients":    "\n".join(
            f"{i.get('amount','')} {i.get('unit','')} {i.get('name','')}".strip()
            for i in info.get("extendedIngredients", [])
        ),
        "instructions":   "\n".join(
            step.get("step", "")
            for block in info.get("analyzedInstructions", [])
            for step in block.get("steps", [])
        ) or info.get("strInstructions", ""),
        "readyInMinutes": info.get("readyInMinutes", 0),
        "servings":       info.get("servings", 1),
        "sourceUrl":      info.get("sourceUrl") or info.get("strSource", ""),
        "creditsText":    info.get("creditsText", ""),
        "imageSourceUrl": info.get("imageSourceUrl", "")
    }

    source = "spoonacular"
    is_saved = False

    if current_user.is_authenticated:
        is_saved = bool(
            SavedRecipe.query.filter_by(
                user_id=current_user.id,
                api_source=source,
                recipe_id=recipe_id
            ).first()
        )

    return render_template(
        "recipe_external.html",
        recipe=recipe,
        recipe_id=recipe_id,
        source=source,
        is_saved=is_saved,
        now=datetime.now(),
        timedelta=timedelta
    )

@app.route("/save/<string:source>/<int:recipe_id>", methods=["POST"])
@login_required
def save_recipe(source, recipe_id):
    info = get_recipe_info(recipe_id)
    if not info:
        return render_template("error.html", message=_("error_default")), 400
    exists = SavedRecipe.query.filter_by(
        user_id=current_user.id,
        api_source=source,
        recipe_id=recipe_id
    ).first()
    if not exists:
        sr = SavedRecipe(
            user_id=current_user.id,
            api_source=source,
            recipe_id=recipe_id,
            title=info.get("title") or info.get("name", "")
        )
        db.session.add(sr)
        db.session.commit()
    return redirect(request.referrer or url_for('index'))


@app.route("/unsave/<string:source>/<int:recipe_id>", methods=["POST"])
@login_required
def unsave_recipe(source, recipe_id):
    entry = SavedRecipe.query.filter_by(
        user_id=current_user.id,
        api_source=source,
        recipe_id=recipe_id
    ).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(request.referrer or url_for('favorites'))


@app.route("/favorites")
@login_required
def favorites():
    saved_entries = SavedRecipe.query.filter_by(
        user_id=current_user.id
    ).order_by(SavedRecipe.saved_at.desc()).all()

    recipes = []
    for e in saved_entries:
        info = get_recipe_info(e.recipe_id)
        if not info:
            continue
        recipes.append({
            "id":       e.recipe_id,
            "title":    info.get("title") or info.get("name", ""),
            "image":    info.get("image", ""),
            "saved_at": e.saved_at,
        })

    return render_template("favorites.html", recipes=recipes)


@app.route("/test-email")
def test_email():
    try:
        response = send_email(
            "jydi93@gmail.com",
            "✅ RecipeFinder Mailgun API Test",
            "Hello! This message was sent using the Mailgun HTTP API from Flask."
        )
        if response.status_code == 200:
            return "✅ Mailgun API email sent successfully!"
        else:
            return f"❌ Mailgun API failed: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Exception: {str(e)}"
    
@app.route("/mealplan/add", methods=["POST"])
@login_required
def add_to_mealplan():
    day = request.form.get("day")
    meal = request.form.get("meal_type")
    recipe_id = request.form.get("recipe_id")
    title = request.form.get("recipe_title")

    if not (day and meal and recipe_id and title):
        flash(_("invalid_day"), "danger")
        return redirect(url_for("index"))

    plan = MealPlan(
        user_id=current_user.id,
        day=day,
        meal_type=meal,
        recipe_id=recipe_id,
        recipe_title=title
    )
    db.session.add(plan)
    db.session.commit()

    flash(_("mealplan_saved"), "success")
    return redirect(url_for("planner.view_meal_plan"))



# (You can still keep your /settings if you like, but language now lives in the navbar)

if __name__ == "__main__":
    app.run(debug=True)
