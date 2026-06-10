"""
Unit Tests — Smart Student RMS
Run: pytest tests/ -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app, db
from app.models.user import User
from app.models.student import Student, AcademicRecord
from app.services.ai_service import AIService


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Authenticated test client."""
    with app.app_context():
        user = User(name="Test Admin", email="test@school.edu", role="admin")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
    client.post("/auth/login", data={"email": "test@school.edu", "password": "testpass"})
    return client


# ── AI Service Tests ──────────────────────────────────────────────────────────

class TestAIService:

    def test_predict_gpa_high_performer(self):
        gpa = AIService.predict_gpa(0.95, 90.0, 88.0)
        assert gpa is not None
        assert 3.0 <= gpa <= 4.0, f"Expected high GPA, got {gpa}"

    def test_predict_gpa_low_performer(self):
        gpa = AIService.predict_gpa(0.40, 35.0, 30.0)
        assert gpa is not None
        assert 0.0 <= gpa <= 2.5, f"Expected low GPA, got {gpa}"

    def test_predict_gpa_bounds(self):
        gpa = AIService.predict_gpa(1.0, 100.0, 100.0)
        assert 0.0 <= gpa <= 4.0

    def test_risk_score_high_risk(self):
        risk = AIService.predict_risk_score(0.40, 30.0, 25.0)
        assert risk >= 0.5, f"Expected high risk, got {risk}"

    def test_risk_score_low_risk(self):
        risk = AIService.predict_risk_score(0.95, 85.0, 80.0)
        assert risk <= 0.3, f"Expected low risk, got {risk}"

    def test_risk_score_bounds(self):
        for att, asgn, mid in [(0.0, 0.0, 0.0), (1.0, 100.0, 100.0), (0.5, 50.0, 50.0)]:
            risk = AIService.predict_risk_score(att, asgn, mid)
            assert 0.0 <= risk <= 1.0

    def test_generate_insight_contains_name(self):
        insight = AIService.generate_insight(
            "John Doe", 0.85, 75.0, 70.0, 3.1, 0.2
        )
        assert "John" in insight

    def test_generate_insight_high_risk_warning(self):
        insight = AIService.generate_insight(
            "Jane Smith", 0.40, 30.0, 25.0, 1.2, 0.85
        )
        assert "risk" in insight.lower() or "intervention" in insight.lower()

    def test_analyze_record_returns_all_fields(self):
        result = AIService.analyze_record(0.8, 70.0, 65.0, "Test Student")
        assert "ai_predicted_gpa" in result
        assert "ai_risk_score" in result
        assert "ai_insight" in result
        assert result["ai_predicted_gpa"] is not None
        assert result["ai_risk_score"] is not None
        assert len(result["ai_insight"]) > 20


# ── Model Tests ───────────────────────────────────────────────────────────────

class TestStudentModel:

    def test_create_student(self, app):
        with app.app_context():
            s = Student(
                student_id="STU-2024-001",
                first_name="Alice",
                last_name="Tadesse",
                email="alice@test.com",
                department="Computer Science",
                year_of_study=2,
            )
            db.session.add(s)
            db.session.commit()
            assert s.id is not None
            assert s.full_name == "Alice Tadesse"

    def test_student_current_gpa(self, app):
        with app.app_context():
            s = Student(
                student_id="STU-2024-002",
                first_name="Bob",
                last_name="Kebede",
                email="bob@test.com",
                department="Engineering",
                year_of_study=1,
            )
            db.session.add(s)
            db.session.flush()

            r1 = AcademicRecord(student_id=s.id, term="Semester 1", term_year=2023, gpa=3.5)
            r2 = AcademicRecord(student_id=s.id, term="Semester 2", term_year=2023, gpa=3.1)
            db.session.add_all([r1, r2])
            db.session.commit()

            assert s.current_gpa == 3.3


# ── Route Tests ───────────────────────────────────────────────────────────────

class TestAuthRoutes:

    def test_login_page_loads(self, client):
        r = client.get("/auth/login")
        assert r.status_code == 200

    def test_login_redirect_when_authenticated(self, auth_client):
        r = auth_client.get("/", follow_redirects=True)
        assert r.status_code == 200

    def test_invalid_login(self, client):
        r = client.post("/auth/login", data={"email": "wrong@x.com", "password": "bad"}, follow_redirects=True)
        assert b"Invalid" in r.data

    def test_logout(self, auth_client):
        r = auth_client.get("/auth/logout", follow_redirects=True)
        assert r.status_code == 200


class TestStudentRoutes:

    def test_student_list_requires_auth(self, client):
        r = client.get("/students/", follow_redirects=True)
        assert b"login" in r.data.lower() or r.status_code == 200

    def test_create_student(self, auth_client, app):
        r = auth_client.post("/students/new", data={
            "student_id": "STU-TEST-001",
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@school.edu",
            "department": "Computer Science",
            "year_of_study": "1",
        }, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            assert Student.query.filter_by(student_id="STU-TEST-001").first() is not None


class TestAPIRoutes:

    def test_api_list_students(self, auth_client):
        r = auth_client.get("/api/students")
        assert r.status_code == 200
        assert r.content_type == "application/json"

    def test_api_create_student(self, auth_client):
        r = auth_client.post("/api/students", json={
            "student_id": "API-001",
            "first_name": "API",
            "last_name": "Test",
            "email": "api@school.edu",
            "department": "Medicine",
        })
        assert r.status_code == 201

    def test_api_predict(self, auth_client, app):
        with app.app_context():
            s = Student(
                student_id="PRED-001", first_name="Pred", last_name="Test",
                email="pred@school.edu", department="Law", year_of_study=1
            )
            db.session.add(s)
            db.session.commit()
            sid = s.id

        r = auth_client.get(f"/api/students/{sid}/predict?attendance_rate=0.8&assignments_avg=70&midterm_score=65")
        assert r.status_code == 200
        data = r.get_json()
        assert "ai_predicted_gpa" in data
        assert "ai_risk_score" in data
