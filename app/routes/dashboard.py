from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.services.analytics_service import AnalyticsService
from app.models.student import Student, AcademicRecord

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.before_request
def block_students():
    """Students have their own portal; keep them out of the staff dashboard."""
    if current_user.is_authenticated and not current_user.is_staff:
        return redirect(url_for("portal.dashboard"))


@dashboard_bp.route("/")
@login_required
def index():
    summary = AnalyticsService.get_dashboard_summary()
    gpa_dist = AnalyticsService.get_gpa_distribution()
    dept_stats = AnalyticsService.get_department_stats()
    risk_breakdown = AnalyticsService.get_risk_breakdown()
    enrollment_trend = AnalyticsService.get_enrollment_trend()

    # Recent at-risk students
    at_risk = (
        Student.query.filter_by(status="at_risk")
        .limit(5).all()
    )

    return render_template(
        "admin/dashboard.html",
        summary=summary,
        gpa_dist=gpa_dist,
        dept_stats=dept_stats,
        risk_breakdown=risk_breakdown,
        enrollment_trend=enrollment_trend,
        at_risk_students=at_risk,
    )
