"""
Database Seeder
===============
Seeds the database with realistic fake data for development/demo.

Run: python scripts/seed_db.py
"""

import sys
import os
import random
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from faker import Faker
from app import create_app, db
from app.models.user import User
from app.models.student import Student, AcademicRecord
from app.services.ai_service import AIService

fake = Faker()
random.seed(42)
Faker.seed(42)

DEPARTMENTS = ["Computer Science", "Business Administration", "Engineering", "Medicine", "Education", "Law"]
PROGRAMS = {
    "Computer Science": ["BSc Computer Science", "BSc Software Engineering", "MSc AI & ML"],
    "Business Administration": ["BBA", "MBA", "BSc Accounting"],
    "Engineering": ["BSc Civil Engineering", "BSc Electrical Engineering", "BSc Mechanical Engineering"],
    "Medicine": ["MBBS", "BSc Nursing", "BSc Pharmacy"],
    "Education": ["BEd", "MEd Educational Psychology"],
    "Law": ["LLB", "LLM"],
}
TERMS = ["Semester 1", "Semester 2"]


def seed_users():
    print("Seeding users...")
    if User.query.filter_by(email="admin@school.edu").first():
        print("  Admin already exists, skipping.")
        return

    admin = User(name="Admin User", email="admin@school.edu", role="admin", department="Administration")
    admin.set_password("admin123")
    db.session.add(admin)

    lecturers = [
        ("Dr. Alice Tesfaye", "alice@school.edu", "Computer Science"),
        ("Prof. James Abebe", "james@school.edu", "Business Administration"),
        ("Dr. Sara Bekele", "sara@school.edu", "Engineering"),
    ]
    for name, email, dept in lecturers:
        u = User(name=name, email=email, role="lecturer", department=dept)
        u.set_password("lecturer123")
        db.session.add(u)

    db.session.commit()
    print("  ✓ 4 users created.")


def seed_students(n=80):
    print(f"Seeding {n} students...")
    if Student.query.first():
        print("  Students already exist, skipping.")
        return
    count = 0
    for i in range(1, n + 1):
        dept = random.choice(DEPARTMENTS)
        program = random.choice(PROGRAMS[dept])
        year = random.randint(1, 4)
        enrollment_year = 2024 - year + 1
        enroll_date = date(enrollment_year, random.choice([1, 9]), random.randint(1, 28))

        student = Student(
            student_id=f"STU-{enrollment_year}-{i:04d}",
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            phone=fake.phone_number()[:20],
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=30),
            gender=random.choice(["Male", "Female"]),
            department=dept,
            program=program,
            year_of_study=year,
            enrollment_date=enroll_date,
            address=fake.address()[:200],
            emergency_contact=fake.phone_number()[:20],
        )
        db.session.add(student)
        db.session.flush()

        # Create 1-4 academic records
        for term_year in range(enrollment_year, min(enrollment_year + year, 2025)):
            for term in TERMS:
                attendance = round(random.betavariate(7, 2), 2)
                assignments = round(random.gauss(68, 15), 1)
                assignments = max(0, min(100, assignments))
                midterm = round(random.gauss(65, 18), 1)
                midterm = max(0, min(100, midterm))
                final = round((assignments * 0.4 + midterm * 0.6) + random.gauss(0, 5), 1)
                final = max(0, min(100, final))
                gpa = round(min((final / 100) * 4.0, 4.0), 2)

                ai_result = AIService.analyze_record(attendance, assignments, midterm, student.full_name)

                record = AcademicRecord(
                    student_id=student.id,
                    term=term,
                    term_year=term_year,
                    attendance_rate=attendance,
                    assignments_avg=assignments,
                    midterm_score=midterm,
                    final_score=final,
                    gpa=gpa,
                    credits_attempted=random.choice([15, 18, 21]),
                    credits_earned=random.choice([12, 15, 18, 21]),
                    **ai_result,
                )
                db.session.add(record)

                # Update status
                if ai_result["ai_risk_score"] > 0.6:
                    student.status = "at_risk"

        count += 1

    db.session.commit()
    print(f"  ✓ {count} students with academic records created.")


def main():
    # Use whatever environment is active (production on Render, development locally).
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        print("=" * 50)
        print("Smart Student RMS — Database Seeder")
        print("=" * 50)
        seed_users()
        seed_students(80)
        print("\n✅ Database seeded successfully!")
        print("\nLogin credentials:")
        print("  Admin:    admin@school.edu / admin123")
        print("  Lecturer: alice@school.edu / lecturer123")
        print("\nRun: python run.py")


if __name__ == "__main__":
    main()
