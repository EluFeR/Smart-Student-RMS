from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    """
    Unified loader for both staff and students.

    Flask-Login stores whatever get_id() returns. Staff ids look like "staff-5",
    student ids like "student-5", so we dispatch on the prefix. Bare integers are
    treated as staff for backward-compatibility with old sessions.
    """
    if isinstance(user_id, str) and user_id.startswith("student-"):
        from app.models.student_account import StudentAccount
        return StudentAccount.query.get(int(user_id.split("-", 1)[1]))

    if isinstance(user_id, str) and user_id.startswith("staff-"):
        user_id = user_id.split("-", 1)[1]
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="lecturer")  # admin, lecturer, viewer
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_staff(self):
        return True

    def get_id(self):
        return f"staff-{self.id}"

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"
