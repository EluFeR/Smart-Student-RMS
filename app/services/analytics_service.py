"""
Analytics Service — computes dashboard metrics and chart data.
"""

from app.models.student import Student, AcademicRecord
from app import db
from sqlalchemy import func
from datetime import datetime


class AnalyticsService:

    @staticmethod
    def get_dashboard_summary():
        """Return key metrics for the admin dashboard."""
        total_students = Student.query.count()
        active_students = Student.query.filter_by(status="active").count()
        at_risk_students = Student.query.filter_by(status="at_risk").count()
        graduated = Student.query.filter_by(status="graduated").count()

        # Average GPA across all records
        avg_gpa_result = db.session.query(func.avg(AcademicRecord.gpa)).scalar()
        avg_gpa = round(avg_gpa_result, 2) if avg_gpa_result else 0.0

        # Average attendance
        avg_att_result = db.session.query(func.avg(AcademicRecord.attendance_rate)).scalar()
        avg_attendance = round((avg_att_result or 0) * 100, 1)

        # High risk count (risk score > 0.6)
        high_risk = AcademicRecord.query.filter(AcademicRecord.ai_risk_score > 0.6).count()

        return {
            "total_students": total_students,
            "active_students": active_students,
            "at_risk_students": at_risk_students,
            "graduated": graduated,
            "avg_gpa": avg_gpa,
            "avg_attendance": avg_attendance,
            "high_risk_count": high_risk,
        }

    @staticmethod
    def get_gpa_distribution():
        """Return GPA distribution buckets for chart rendering."""
        records = AcademicRecord.query.filter(AcademicRecord.gpa.isnot(None)).all()
        buckets = {"0.0–1.0": 0, "1.0–2.0": 0, "2.0–3.0": 0, "3.0–3.5": 0, "3.5–4.0": 0}
        for r in records:
            if r.gpa < 1.0:
                buckets["0.0–1.0"] += 1
            elif r.gpa < 2.0:
                buckets["1.0–2.0"] += 1
            elif r.gpa < 3.0:
                buckets["2.0–3.0"] += 1
            elif r.gpa < 3.5:
                buckets["3.0–3.5"] += 1
            else:
                buckets["3.5–4.0"] += 1
        return buckets

    @staticmethod
    def get_department_stats():
        """Return average GPA and student count per department."""
        results = (
            db.session.query(
                Student.department,
                func.count(Student.id).label("count"),
                func.avg(AcademicRecord.gpa).label("avg_gpa"),
            )
            .outerjoin(AcademicRecord, Student.id == AcademicRecord.student_id)
            .group_by(Student.department)
            .all()
        )
        return [
            {
                "department": r.department,
                "count": r.count,
                "avg_gpa": round(r.avg_gpa, 2) if r.avg_gpa else 0.0,
            }
            for r in results
        ]

    @staticmethod
    def get_enrollment_trend():
        """Return student enrollment count by year.

        Grouped in Python rather than with a DB date function so it works on both
        SQLite (dev) and Postgres (prod) — SQLite's strftime() doesn't exist on Postgres.
        """
        counts = {}
        for (enroll_date,) in db.session.query(Student.enrollment_date).all():
            if not enroll_date:
                continue
            year = str(enroll_date.year)
            counts[year] = counts.get(year, 0) + 1
        return [{"year": year, "count": counts[year]} for year in sorted(counts)]

    @staticmethod
    def get_risk_breakdown():
        """Return count of students by risk level."""
        records = AcademicRecord.query.filter(AcademicRecord.ai_risk_score.isnot(None)).all()
        breakdown = {"low": 0, "moderate": 0, "high": 0}
        seen = set()
        for r in records:
            if r.student_id in seen:
                continue
            seen.add(r.student_id)
            if r.ai_risk_score < 0.3:
                breakdown["low"] += 1
            elif r.ai_risk_score < 0.6:
                breakdown["moderate"] += 1
            else:
                breakdown["high"] += 1
        return breakdown
