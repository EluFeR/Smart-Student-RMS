from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class StudentAccount(UserMixin, db.Model):
    """
    Login identity for a student.

    This is intentionally SEPARATE from the Student data record (app.models.student).
    Staff create the Student record (the grades/attendance live there); a student then
    signs up for an *account* to view that record. The account is only approved if a
    matching Student record already exists — i.e. staff added them first.
    """
    __tablename__ = "student_accounts"

    id = db.Column(db.Integer, primary_key=True)
    # The student-facing ID printed on their card, e.g. STU-2024-0007. Used to match.
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Link to the data record staff created. Null until/if matched.
    student_pk = db.Column(db.Integer, db.ForeignKey("students.id"))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    student = db.relationship("Student", backref="account")

    # --- Flask-Login: prefix the session id so the loader can tell accounts apart ---
    def get_id(self):
        return f"student-{self.id}"

    @property
    def is_staff(self):
        return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<StudentAccount {self.student_id} approved={self.is_approved}>"
