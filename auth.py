import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User

auth_bp = Blueprint("auth", __name__)
mail = Mail()
ts = None  # Token serializer

# --- One-time Flask app config hook ---
@auth_bp.record_once
def on_register(state):
    app = state.app
    app.config.update(
        MAIL_SERVER         = os.getenv("MAIL_SERVER"),
        MAIL_PORT           = int(os.getenv("MAIL_PORT", 587)),
        MAIL_USE_TLS        = True,
        MAIL_USERNAME       = os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD       = os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    )
    mail.init_app(app)

    global ts
    ts = URLSafeTimedSerializer(app.secret_key)

# --- Helpers ---
def generate_token(email, salt):
    return ts.dumps(email, salt=salt)

def verify_token(token, salt, expiration=3600):
    try:
        return ts.loads(token, salt=salt, max_age=expiration)
    except (BadSignature, SignatureExpired):
        return None

# --- Signup ---
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if not username or not email or not password or not confirm:
            flash("Please fill in all fields", "danger")
            return render_template("signup.html")
        if password != confirm:
            flash("Passwords do not match", "danger")
            return render_template("signup.html")

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists", "danger")
            return render_template("signup.html")

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_verified=False
        )
        db.session.add(user)
        db.session.commit()

        token = generate_token(email, "email-verify-salt")
        verify_url = url_for("auth.verify_account", token=token, _external=True)

        lang = session.get("language", "en")
        msg = Message("Verify your account", recipients=[email])
        msg.body = f"Click to verify your account: {verify_url}"
        msg.html = render_template(f"email/{lang}/verify_email.html", verify_url=verify_url)
        mail.send(msg)

        flash("Account created! Please check your email to verify.", "info")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")

# --- Login ---
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash("Please verify your email before logging in.", "warning")
                return render_template("login.html")
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash("Invalid credentials.", "danger")
    return render_template("login.html")

# --- Logout ---
@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

# --- Email Verification ---
@auth_bp.route("/verify/<token>")
def verify_account(token):
    email = verify_token(token, "email-verify-salt")
    if not email:
        flash("Invalid or expired verification link.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if user:
        user.is_verified = True
        db.session.commit()
        flash("Your account is now verified!", "success")
    else:
        flash("User not found.", "danger")
    return redirect(url_for("auth.login"))

@auth_bp.route("/resend_verification", methods=["GET", "POST"])
def resend_verification():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            if user.is_verified:
                flash("Your account is already verified.", "info")
                return redirect(url_for("auth.login"))

            token = generate_token(email, "email-verify-salt")
            verify_url = url_for("auth.verify_account", token=token, _external=True)

            lang = session.get("language", "en")
            msg = Message("Verify your account", recipients=[user.email])
            msg.body = f"Click to verify your account: {verify_url}"
            msg.html = render_template(f"email/{lang}/verify_email.html", verify_url=verify_url)
            mail.send(msg)

            flash("Verification email sent again. Check your inbox.", "info")
        else:
            flash("No account found with that email.", "danger")

        return redirect(url_for("auth.login"))

    return render_template("resend_verification.html")

# --- Password Reset ---
@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_token(email, "password-reset-salt")
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            lang = session.get("language", "en")
            msg = Message("Password Reset", recipients=[email])
            msg.body = f"Click to reset your password: {reset_url}"
            msg.html = render_template(f"email/{lang}/reset_email.html", reset_url=reset_url)
            mail.send(msg)

        flash("If that email exists, instructions have been sent.", "info")
        return redirect(url_for("auth.login"))

    return render_template("reset_request.html")

@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = ts.loads(token, salt="password-reset-salt", max_age=3600)
    except Exception as e:
        flash("Invalid or expired token.", "danger")
        return redirect(url_for("auth.reset_request"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if not password or not confirm:
            flash("Please fill out all fields.", "danger")
            return render_template("reset_token.html")  # Match your filename

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("reset_token.html")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for("auth.reset_request"))

        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash("Your password has been updated.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_token.html")

