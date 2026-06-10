"""
Report Service — generates PDF student reports using ReportLab.
"""

import os
import csv
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.models.student import Student, AcademicRecord


class ReportService:

    @staticmethod
    def generate_student_pdf(student: Student) -> bytes:
        """Generate a PDF report for a single student."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not installed. Run: pip install reportlab")

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18,
                                     textColor=colors.HexColor("#1a73e8"), spaceAfter=6)
        story.append(Paragraph("Student Academic Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M')}", styles["Normal"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.4*cm))

        # Student info
        story.append(Paragraph("Student Information", styles["Heading2"]))
        info_data = [
            ["Student ID", student.student_id, "Name", student.full_name],
            ["Department", student.department, "Program", student.program or "—"],
            ["Year of Study", str(student.year_of_study or "—"), "Status", student.status.upper()],
            ["Email", student.email, "Current GPA", str(student.current_gpa or "—")],
        ]
        info_table = Table(info_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8f0fe")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#e8f0fe")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))

        # Academic records
        if student.records:
            story.append(Paragraph("Academic Records", styles["Heading2"]))
            headers = ["Term", "Year", "Attendance", "Assignments", "Midterm", "Final", "GPA", "AI Pred. GPA", "Risk"]
            rows = [headers]
            for r in sorted(student.records, key=lambda x: x.term_year):
                rows.append([
                    r.term,
                    str(r.term_year),
                    f"{int((r.attendance_rate or 0) * 100)}%",
                    f"{r.assignments_avg:.1f}" if r.assignments_avg else "—",
                    f"{r.midterm_score:.1f}" if r.midterm_score else "—",
                    f"{r.final_score:.1f}" if r.final_score else "—",
                    f"{r.gpa:.2f}" if r.gpa else "—",
                    f"{r.ai_predicted_gpa:.2f}" if r.ai_predicted_gpa else "—",
                    f"{int((r.ai_risk_score or 0) * 100)}%",
                ])
            rec_table = Table(rows, repeatRows=1)
            rec_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a73e8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(rec_table)
            story.append(Spacer(1, 0.5*cm))

            # AI Insights
            story.append(Paragraph("AI Insights", styles["Heading2"]))
            for r in sorted(student.records, key=lambda x: x.term_year, reverse=True)[:3]:
                if r.ai_insight:
                    story.append(Paragraph(f"<b>{r.term} {r.term_year}:</b> {r.ai_insight}", styles["Normal"]))
                    story.append(Spacer(1, 0.3*cm))

        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def export_students_csv(students: list, output_path: str):
        """Export student list to CSV."""
        fieldnames = [
            "student_id", "full_name", "email", "department",
            "program", "year_of_study", "status", "current_gpa", "enrollment_date"
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in students:
                writer.writerow({
                    "student_id": s.student_id,
                    "full_name": s.full_name,
                    "email": s.email,
                    "department": s.department,
                    "program": s.program,
                    "year_of_study": s.year_of_study,
                    "status": s.status,
                    "current_gpa": s.current_gpa,
                    "enrollment_date": s.enrollment_date,
                })
        return output_path
