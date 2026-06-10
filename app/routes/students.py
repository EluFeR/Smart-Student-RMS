from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from app import db
from app.models.student import Student, AcademicRecord
from app.services.ai_service import AIService
from app.services.report_service import ReportService
from datetime import date
import io

students_bp = Blueprint("students", __name__)


@students_bp.before_request
def block_students():
    """Student records are staff-only; students use the portal to view their own."""
    if current_user.is_authenticated and not current_user.is_staff:
        return redirect(url_for("portal.dashboard"))


def _parse_date(val):
    try:
        return date.fromisoformat(val) if val else None
    except ValueError:
        return None


@students_bp.route("/")
@login_required
def list_students():
    search = request.args.get("q", "").strip()
    dept = request.args.get("dept", "")
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    query = Student.query
    if search:
        query = query.filter(
            db.or_(
                Student.first_name.ilike(f"%{search}%"),
                Student.last_name.ilike(f"%{search}%"),
                Student.student_id.ilike(f"%{search}%"),
                Student.email.ilike(f"%{search}%"),
            )
        )
    if dept:
        query = query.filter_by(department=dept)
    if status:
        query = query.filter_by(status=status)

    students = query.order_by(Student.last_name).paginate(page=page, per_page=20)
    departments = db.session.query(Student.department).distinct().all()

    return render_template(
        "students/list.html",
        students=students,
        departments=[d[0] for d in departments],
        search=search, dept=dept, status=status,
    )


@students_bp.route("/<int:student_id>")
@login_required
def student_detail(student_id):
    student = Student.query.get_or_404(student_id)
    records = sorted(student.records, key=lambda r: r.term_year, reverse=True)
    return render_template("students/detail.html", student=student, records=records)


@students_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_student():
    if request.method == "POST":
        f = request.form
        student = Student(
            student_id=f.get("student_id"),
            first_name=f.get("first_name"),
            last_name=f.get("last_name"),
            email=f.get("email"),
            phone=f.get("phone"),
            gender=f.get("gender"),
            department=f.get("department"),
            program=f.get("program"),
            year_of_study=int(f.get("year_of_study", 1)),
            enrollment_date=_parse_date(f.get("enrollment_date")) or date.today(),
            address=f.get("address"),
            emergency_contact=f.get("emergency_contact"),
        )
        db.session.add(student)
        db.session.commit()
        flash(f"Student {student.full_name} added successfully.", "success")
        return redirect(url_for("students.student_detail", student_id=student.id))

    return render_template("students/form.html", student=None)


@students_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        f = request.form
        student.first_name = f.get("first_name", student.first_name)
        student.last_name = f.get("last_name", student.last_name)
        student.email = f.get("email", student.email)
        student.phone = f.get("phone", student.phone)
        student.department = f.get("department", student.department)
        student.program = f.get("program", student.program)
        student.year_of_study = int(f.get("year_of_study", student.year_of_study))
        student.status = f.get("status", student.status)
        student.address = f.get("address", student.address)
        db.session.commit()
        flash("Student record updated.", "success")
        return redirect(url_for("students.student_detail", student_id=student.id))

    return render_template("students/form.html", student=student)


@students_bp.route("/<int:student_id>/delete", methods=["POST"])
@login_required
def delete_student(student_id):
    if not current_user.is_admin:
        flash("Only admins can delete student records.", "danger")
        return redirect(url_for("students.list_students"))
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash(f"Student {student.full_name} removed.", "info")
    return redirect(url_for("students.list_students"))


@students_bp.route("/<int:student_id>/records/new", methods=["GET", "POST"])
@login_required
def add_record(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        f = request.form
        attendance = float(f.get("attendance_rate", 0))
        assignments = float(f.get("assignments_avg", 0))
        midterm = float(f.get("midterm_score", 0))
        final = float(f.get("final_score", 0)) if f.get("final_score") else None

        # Compute GPA from final if provided
        gpa = None
        if final is not None:
            gpa = round(min((final / 100) * 4.0, 4.0), 2)

        # AI analysis
        ai_result = AIService.analyze_record(attendance, assignments, midterm, student.full_name)

        record = AcademicRecord(
            student_id=student.id,
            term=f.get("term"),
            term_year=int(f.get("term_year")),
            attendance_rate=attendance,
            assignments_avg=assignments,
            midterm_score=midterm,
            final_score=final,
            gpa=gpa,
            credits_attempted=int(f.get("credits_attempted", 0)),
            credits_earned=int(f.get("credits_earned", 0)),
            remarks=f.get("remarks"),
            **ai_result,
        )
        db.session.add(record)

        # Auto-update student status
        if ai_result["ai_risk_score"] > 0.6:
            student.status = "at_risk"
        elif student.status == "at_risk" and ai_result["ai_risk_score"] < 0.3:
            student.status = "active"

        db.session.commit()
        flash("Academic record added with AI analysis.", "success")
        return redirect(url_for("students.student_detail", student_id=student.id))

    return render_template("students/record_form.html", student=student)


@students_bp.route("/<int:student_id>/report")
@login_required
def download_report(student_id):
    student = Student.query.get_or_404(student_id)
    try:
        pdf_bytes = ReportService.generate_student_pdf(student)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"report_{student.student_id}.pdf",
        )
    except Exception as e:
        flash(f"Report generation failed: {e}", "danger")
        return redirect(url_for("students.student_detail", student_id=student.id))
