from app import db
from datetime import datetime


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # e.g. STU-2024-001
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    department = db.Column(db.String(100), nullable=False)
    program = db.Column(db.String(100))
    year_of_study = db.Column(db.Integer)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default="active")  # active, at_risk, graduated, withdrawn
    photo_url = db.Column(db.String(200))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    records = db.relationship("AcademicRecord", backref="student", lazy=True, cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def latest_record(self):
        if self.records:
            return sorted(self.records, key=lambda r: r.term_year, reverse=True)[0]
        return None

    @property
    def current_gpa(self):
        if self.records:
            gpas = [r.gpa for r in self.records if r.gpa is not None]
            return round(sum(gpas) / len(gpas), 2) if gpas else None
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "department": self.department,
            "program": self.program,
            "year_of_study": self.year_of_study,
            "status": self.status,
            "current_gpa": self.current_gpa,
            "enrollment_date": self.enrollment_date.isoformat() if self.enrollment_date else None,
        }

    def __repr__(self):
        return f"<Student {self.student_id}: {self.full_name}>"


class AcademicRecord(db.Model):
    __tablename__ = "academic_records"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    term = db.Column(db.String(20), nullable=False)   # e.g. "Semester 1", "Q2"
    term_year = db.Column(db.Integer, nullable=False)
    attendance_rate = db.Column(db.Float)             # 0.0 – 1.0
    assignments_avg = db.Column(db.Float)             # 0 – 100
    midterm_score = db.Column(db.Float)               # 0 – 100
    final_score = db.Column(db.Float)                 # 0 – 100
    gpa = db.Column(db.Float)                         # 0.0 – 4.0
    credits_attempted = db.Column(db.Integer)
    credits_earned = db.Column(db.Integer)
    remarks = db.Column(db.Text)
    ai_risk_score = db.Column(db.Float)               # 0.0 – 1.0, from ML model
    ai_predicted_gpa = db.Column(db.Float)            # ML prediction
    ai_insight = db.Column(db.Text)                   # NLG summary
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "term": self.term,
            "term_year": self.term_year,
            "attendance_rate": self.attendance_rate,
            "assignments_avg": self.assignments_avg,
            "midterm_score": self.midterm_score,
            "final_score": self.final_score,
            "gpa": self.gpa,
            "credits_attempted": self.credits_attempted,
            "credits_earned": self.credits_earned,
            "ai_risk_score": self.ai_risk_score,
            "ai_predicted_gpa": self.ai_predicted_gpa,
            "ai_insight": self.ai_insight,
        }

    def __repr__(self):
        return f"<AcademicRecord Student:{self.student_id} {self.term} {self.term_year}>"
