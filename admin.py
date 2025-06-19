# admin.py

from flask import Blueprint, request, flash, redirect, url_for, render_template
from werkzeug.security import check_password_hash
from flask_login import login_required, current_user
from models import db, User, AuditLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
@login_required
def restrict_admin():
    if not current_user.is_admin:
        return "403 Forbidden", 403

@admin_bp.route("/")
def dashboard():
    total_users = User.query.count()
    total_verified = User.query.filter_by(is_verified=True).count()
    recent_logins = User.query.order_by(User.last_login.desc()).limit(10).all()
    recent_visits = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(15).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_verified=total_verified,
        recent_logins=recent_logins,
        recent_visits=recent_visits
    )

@admin_bp.route("/users")
@login_required
def user_list():
    if not current_user.is_admin:
        abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/user_list.html", users=users)

@admin_bp.route("/logs")
@login_required
def visit_logs():
    if not current_user.is_admin:
        abort(403)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()
    return render_template("admin/logs.html", logs=logs)

@admin_bp.route("/admin/delete/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if not current_user.is_owner:
        abort(403)
    if not check_password_hash(current_user.password_hash, request.form.get("admin_password")):
        flash("Incorrect password", "danger")
        return redirect(url_for("admin.user_list"))

@admin_bp.route("/toggle_admin/<int:user_id>", methods=["POST"])
@login_required
def toggle_admin(user_id):
    if not current_user.is_owner:
        return "403 Forbidden", 403

    user = User.query.get_or_404(user_id)
    if user.is_owner:
        flash("You cannot change owner permissions.", "danger")
        return redirect(url_for("admin.user_list"))

    user.is_admin = not user.is_admin
    db.session.add(AuditLog(
        event_type="admin_toggle",
        user_id=current_user.id,
        details=f"Toggled admin for {user.username} to {user.is_admin}"
    ))
    db.session.commit()
    flash(f"Admin status {'granted' if user.is_admin else 'revoked'} for {user.username}.", "success")
    return redirect(url_for("admin.user_list"))


@admin_bp.route("/make_owner/<int:user_id>", methods=["POST"])
def make_owner(user_id):
    existing_owner = User.query.filter_by(is_owner=True).first()
    if existing_owner and existing_owner.id != user_id:
        flash("Only one owner allowed. Revoke current owner first.", "danger")
        return redirect(url_for("admin.user_list"))

    user = User.query.get_or_404(user_id)
    user.is_owner = True
    db.session.commit()
    db.session.add(AuditLog(event_type="make_owner", user_id=current_user.id, details=f"Made {user.username} the owner"))
    db.session.commit()
    return redirect(url_for("admin.user_list"))
