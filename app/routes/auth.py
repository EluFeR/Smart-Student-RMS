from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.student_account import StudentAccount
from app import db
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index") if current_user.is_staff
                        else url_for("portal.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        # Try staff first.
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(next_page or url_for("dashboard.index"))

        # Otherwise try a student account — same form, routed automatically.
        account = StudentAccount.query.filter_by(email=email).first()
        if account and account.check_password(password):
            if not account.is_approved:
                flash("Your account is pending approval. Staff must add you as a student first.", "warning")
                return render_template("auth/login.html")
            login_user(account, remember=remember)
            account.last_login = datetime.utcnow()
            db.session.commit()
            flash(f"Welcome back!", "success")
            return redirect(url_for("portal.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if not current_user.is_admin:
        flash("Only admins can create new accounts.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "lecturer")
        department = request.form.get("department", "")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
        else:
            user = User(name=name, email=email, role=role, department=department)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f"Account created for {name}.", "success")
            return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")
