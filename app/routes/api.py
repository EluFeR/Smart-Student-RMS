"""
REST API — JSON endpoints for external integration.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required
from app import db
from app.models.student import Student, AcademicRecord
from app.services.ai_service import AIService
from app.services.analytics_service import AnalyticsService

api_bp = Blueprint("api", __name__)


def _error(message, status=400):
    return jsonify({"error": message}), status


# ── Students ──────────────────────────────────────────────────────────────────

@api_bp.route("/students", methods=["GET"])
@login_required
def api_list_students():
    students = Student.query.all()
    return jsonify([s.to_dict() for s in students])


@api_bp.route("/students/<int:student_id>", methods=["GET"])
@login_required
def api_get_student(student_id):
    student = Student.query.get_or_404(student_id)
    data = student.to_dict()
    data["records"] = [r.to_dict() for r in student.records]
    return jsonify(data)


@api_bp.route("/students", methods=["POST"])
@login_required
def api_create_student():
    data = request.get_json()
    if not data:
        return _error("No JSON body provided.")
    required = ["student_id", "first_name", "last_name", "email", "department"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return _error(f"Missing required fields: {', '.join(missing)}")
    if Student.query.filter_by(student_id=data["student_id"]).first():
        return _error("Student ID already exists.", 409)
    student = Student(**{k: data.get(k) for k in [
        "student_id", "first_name", "last_name", "email", "phone",
        "department", "program", "year_of_study", "gender",
    ]})
    db.session.add(student)
    db.session.commit()
    return jsonify(student.to_dict()), 201


@api_bp.route("/students/<int:student_id>", methods=["PUT"])
@login_required
def api_update_student(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.get_json() or {}
    for field in ["first_name", "last_name", "email", "phone", "department",
                  "program", "year_of_study", "status"]:
        if field in data:
            setattr(student, field, data[field])
    db.session.commit()
    return jsonify(student.to_dict())


@api_bp.route("/students/<int:student_id>", methods=["DELETE"])
@login_required
def api_delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": f"Student {student_id} deleted."})


# ── AI Prediction ─────────────────────────────────────────────────────────────

@api_bp.route("/students/<int:student_id>/predict", methods=["GET"])
@login_required
def api_predict(student_id):
    student = Student.query.get_or_404(student_id)
    att = request.args.get("attendance_rate", type=float)
    asgn = request.args.get("assignments_avg", type=float)
    mid = request.args.get("midterm_score", type=float)

    if None in (att, asgn, mid):
        return _error("Provide attendance_rate, assignments_avg, midterm_score as query params.")

    result = AIService.analyze_record(att, asgn, mid, student.full_name)
    return jsonify({
        "student_id": student_id,
        "student_name": student.full_name,
        "input": {"attendance_rate": att, "assignments_avg": asgn, "midterm_score": mid},
        **result,
    })


# ── Analytics ─────────────────────────────────────────────────────────────────

@api_bp.route("/analytics/summary", methods=["GET"])
@login_required
def api_analytics_summary():
    return jsonify({
        "summary": AnalyticsService.get_dashboard_summary(),
        "gpa_distribution": AnalyticsService.get_gpa_distribution(),
        "department_stats": AnalyticsService.get_department_stats(),
        "risk_breakdown": AnalyticsService.get_risk_breakdown(),
        "enrollment_trend": AnalyticsService.get_enrollment_trend(),
    })
