"""
Student Portal
==============
The student-facing side of the app. Students sign up, the system checks whether
staff have already added them as a Student record, and approves or rejects on that
basis. Once approved they log in to a read-only dashboard of their own scores,
attendance, and AI insights — everything staff filled in about them.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import logout_user, login_required, current_user
from app import db
from app.models.student import Student
from app.models.student_account import StudentAccount

portal_bp = Blueprint("portal", __name__)


def _student_required():
    """Block staff (or anonymous) from student-only pages."""
    return current_user.is_authenticated and not current_user.is_staff


@portal_bp.route("/login")
def login():
    """Login is unified under the staff page now — this just redirects there."""
    return redirect(url_for("auth.login"))


@portal_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated and not current_user.is_staff:
        return redirect(url_for("portal.dashboard"))

    if request.method == "POST":
        student_id = request.form.get("student_id", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not (student_id and email and password):
            flash("All fields are required.", "warning")
            return render_template("portal/signup.html")

        if StudentAccount.query.filter((StudentAccount.email == email) |
                                       (StudentAccount.student_id == student_id)).first():
            flash("An account with that Student ID or email already exists. Try logging in.", "warning")
            return render_template("portal/signup.html")

        # --- The approval check ---
        # The system approves ONLY if staff already added a matching student record.
        # We match on Student ID AND email so a student can't claim someone else's record.
        record = Student.query.filter_by(student_id=student_id).first()
        matched = record is not None and record.email.strip().lower() == email

        account = StudentAccount(student_id=student_id, email=email)
        account.set_password(password)

        if matched:
            account.student_pk = record.id
            account.is_approved = True
            db.session.add(account)
            db.session.commit()
            flash("✅ Verified against school records — your account is approved. Please log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            # No matching staff record → rejected. Nothing is saved.
            flash(
                "❌ We couldn't find you in the school records. "
                "Make sure your Student ID and email exactly match what the academic office registered. "
                "If you were just enrolled, please try again later.",
                "danger",
            )
            return render_template("portal/signup.html")

    return render_template("portal/signup.html")


@portal_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_staff:
        return redirect(url_for("dashboard.index"))

    student = current_user.student
    if student is None:
        flash("Your record could not be found. Please contact the academic office.", "danger")
        return redirect(url_for("portal.login"))

    records = sorted(student.records, key=lambda r: (r.term_year, r.term), reverse=True)
    return render_template("portal/dashboard.html", student=student, records=records)


@portal_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("portal.login"))
