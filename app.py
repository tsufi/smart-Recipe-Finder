import os
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request,
    redirect, url_for, session
)
from services.email_service import send_email
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer

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
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

# 9) Instantiate Translator
from utils.translator import Translator
translator = Translator()  # defaults to ./lang/{code}.json

# 10) Load per-request language
@app.before_request
def _load_language():
    lang = session.get("language", "en")
    translator.load_language(lang)

# 11) Inject helpers into templates
@app.context_processor
def _inject_globals():
    return {
        "_": translator._,        # translation func
        "LANGUAGES": LANGUAGES,   # for your navbar dropdown
        "current_language": session.get("language", "en"),
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
                              step.get("step","")
                              for block in info.get("analyzedInstructions", [])
                              for step in block.get("steps", [])
                          ) or info.get("strInstructions",""),
        "readyInMinutes": info.get("readyInMinutes", 0),
        "servings":       info.get("servings", 1),
        "sourceUrl":      info.get("sourceUrl") or info.get("strSource","")
    }

    source = "spoonacular"
    is_saved = False
    if 'user_id' in session:
        is_saved = bool(
            SavedRecipe.query.filter_by(
                user_id=session['user_id'],
                api_source=source,
                recipe_id=recipe_id
            ).first()
        )

    return render_template(
        "recipe_external.html",
        recipe=recipe,
        recipe_id=recipe_id,
        source=source,
        is_saved=is_saved
    )

@app.route("/save/<string:source>/<int:recipe_id>", methods=["POST"])
def save_recipe(source, recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    info = get_recipe_info(recipe_id)
    if not info:
        return render_template("error.html", message=_("error_default")), 400
    exists = SavedRecipe.query.filter_by(
        user_id=session['user_id'],
        api_source=source,
        recipe_id=recipe_id
    ).first()
    if not exists:
        sr = SavedRecipe(
            user_id=session['user_id'],
            api_source=source,
            recipe_id=recipe_id,
            title=info.get("title") or info.get("name","")
        )
        db.session.add(sr)
        db.session.commit()
    return redirect(request.referrer or url_for('index'))

@app.route("/unsave/<string:source>/<int:recipe_id>", methods=["POST"])
def unsave_recipe(source, recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    entry = SavedRecipe.query.filter_by(
        user_id=session['user_id'],
        api_source=source,
        recipe_id=recipe_id
    ).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return redirect(request.referrer or url_for('favorites'))

@app.route("/favorites")
def favorites():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    saved_entries = SavedRecipe.query.filter_by(
        user_id=session['user_id']
    ).order_by(SavedRecipe.saved_at.desc()).all()

    recipes = []
    for e in saved_entries:
        info = get_recipe_info(e.recipe_id)
        if not info:
            continue
        recipes.append({
            "id":       e.recipe_id,
            "title":    info.get("title") or info.get("name", ""),
            "image":    info.get("image",""),
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

# (You can still keep your /settings if you like, but language now lives in the navbar)

if __name__ == "__main__":
    app.run(debug=True)
