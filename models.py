"""Database models for the RecipeFinder application."""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Date
# Initialize SQLAlchemy
db = SQLAlchemy()

class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class Favorite(db.Model):
    __tablename__ = "favorites"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    added_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    recipe = db.relationship('Recipe', backref=db.backref('favorites', cascade='all, delete'))

class Setting(db.Model):
    __tablename__ = "settings"
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.String(255), nullable=False)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_owner = db.Column(db.Boolean, default=False)  # only one can be true

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    preferred_language = db.Column(db.String(10), default='en')


    saved = db.relationship('SavedRecipe', backref='user', lazy=True)
    plans = db.relationship('MealPlan', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class SavedRecipe(db.Model):
    __tablename__ = "saved_recipes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipe_id = db.Column(db.Integer)
    api_source = db.Column(db.String(50))
    title = db.Column(db.String(255))
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

class MealPlan(db.Model):
    __tablename__ = "meal_plan"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    day = db.Column(db.String(10))  # e.g. "monday"
    meal_type = db.Column(db.String(20))  # e.g. "breakfast"
    recipe_id = db.Column(db.Integer)
    recipe_title = db.Column(db.String(255))
    
class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    event_type = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    details = db.Column(db.Text, nullable=True)
    # Optional relationship back to user
    user = db.relationship('User', backref=db.backref('audit_logs', cascade='all, delete-orphan'))

def log_event(event_type, user_id=None, details=None):
    from app import db  # or wherever db is correctly imported
    log = AuditLog(
        event_type=event_type,
        user_id=user_id,
        details=details
    )
    db.session.add(log)
    db.session.commit()