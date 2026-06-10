"""
AI Service — handles ML predictions, at-risk detection, and NLG insight generation.
Models are loaded once at startup and reused across requests.
"""

import os
import joblib
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models")


class AIService:
    _gpa_predictor = None
    _risk_classifier = None
    _models_loaded = False

    @classmethod
    def load_models(cls):
        """Load trained ML models from disk. Falls back gracefully if not found."""
        gpa_path = os.path.join(MODEL_DIR, "gpa_predictor.pkl")
        risk_path = os.path.join(MODEL_DIR, "risk_classifier.pkl")

        try:
            if os.path.exists(gpa_path):
                cls._gpa_predictor = joblib.load(gpa_path)
                logger.info("GPA predictor model loaded.")
            else:
                logger.warning("GPA predictor model not found. Run ml/train_model.py first.")

            if os.path.exists(risk_path):
                cls._risk_classifier = joblib.load(risk_path)
                logger.info("Risk classifier model loaded.")
            else:
                logger.warning("Risk classifier model not found. Run ml/train_model.py first.")

            cls._models_loaded = True
        except Exception as e:
            logger.error(f"Error loading models: {e}")

    @classmethod
    def _build_features(cls, attendance_rate: float, assignments_avg: float, midterm_score: float) -> np.ndarray:
        """Build feature vector for the ML model."""
        attendance_pct = attendance_rate * 100
        study_index = (assignments_avg * 0.4 + midterm_score * 0.6)
        return np.array([[attendance_pct, assignments_avg, midterm_score, study_index]])

    @classmethod
    def predict_gpa(cls, attendance_rate: float, assignments_avg: float, midterm_score: float) -> Optional[float]:
        """Predict end-of-term GPA using the trained Random Forest model."""
        if cls._gpa_predictor is None:
            # Fallback: simple weighted formula
            predicted = (
                attendance_rate * 0.2 * 4.0
                + (assignments_avg / 100) * 0.3 * 4.0
                + (midterm_score / 100) * 0.5 * 4.0
            )
            return round(min(max(predicted, 0.0), 4.0), 2)
        try:
            features = cls._build_features(attendance_rate, assignments_avg, midterm_score)
            prediction = cls._gpa_predictor.predict(features)[0]
            return round(float(np.clip(prediction, 0.0, 4.0)), 2)
        except Exception as e:
            logger.error(f"GPA prediction error: {e}")
            return None

    @classmethod
    def predict_risk_score(cls, attendance_rate: float, assignments_avg: float, midterm_score: float) -> float:
        """Return a risk score between 0.0 (safe) and 1.0 (high risk)."""
        if cls._risk_classifier is None:
            # Fallback heuristic
            score = 0.0
            if attendance_rate < 0.6:
                score += 0.4
            if assignments_avg < 50:
                score += 0.3
            if midterm_score < 50:
                score += 0.3
            return round(min(score, 1.0), 2)
        try:
            features = cls._build_features(attendance_rate, assignments_avg, midterm_score)
            prob = cls._risk_classifier.predict_proba(features)[0][1]
            return round(float(prob), 2)
        except Exception as e:
            logger.error(f"Risk prediction error: {e}")
            return 0.0

    @classmethod
    def generate_insight(
        cls,
        student_name: str,
        attendance_rate: float,
        assignments_avg: float,
        midterm_score: float,
        predicted_gpa: float,
        risk_score: float,
    ) -> str:
        """
        Generate a natural language insight summary for a student.
        Uses rule-based NLG with conditional templates.
        """
        first_name = student_name.split()[0]
        attendance_pct = int(attendance_rate * 100)

        # Attendance commentary
        if attendance_rate >= 0.9:
            attendance_comment = f"{first_name} has excellent attendance at {attendance_pct}%."
        elif attendance_rate >= 0.75:
            attendance_comment = f"{first_name} maintains good attendance at {attendance_pct}%."
        elif attendance_rate >= 0.6:
            attendance_comment = f"{first_name}'s attendance is below average at {attendance_pct}%, which may impact performance."
        else:
            attendance_comment = f"⚠️ {first_name}'s attendance is critically low at {attendance_pct}%. Immediate intervention is recommended."

        # Academic performance commentary
        avg_score = (assignments_avg + midterm_score) / 2
        if avg_score >= 80:
            performance_comment = f"Academic scores are strong (assignments: {assignments_avg:.1f}, midterm: {midterm_score:.1f})."
        elif avg_score >= 65:
            performance_comment = f"Academic scores are satisfactory (assignments: {assignments_avg:.1f}, midterm: {midterm_score:.1f}), with room for improvement."
        elif avg_score >= 50:
            performance_comment = f"Academic scores are below expectations (assignments: {assignments_avg:.1f}, midterm: {midterm_score:.1f}). Additional support is advised."
        else:
            performance_comment = f"⚠️ Academic scores are critically low (assignments: {assignments_avg:.1f}, midterm: {midterm_score:.1f}). Urgent academic counseling recommended."

        # GPA prediction commentary
        if predicted_gpa >= 3.5:
            gpa_comment = f"The AI model predicts a final GPA of {predicted_gpa:.2f} — an excellent outcome."
        elif predicted_gpa >= 3.0:
            gpa_comment = f"The AI model predicts a final GPA of {predicted_gpa:.2f} — a solid performance."
        elif predicted_gpa >= 2.0:
            gpa_comment = f"The AI model predicts a final GPA of {predicted_gpa:.2f}. Focused effort in remaining assessments can improve this."
        else:
            gpa_comment = f"The AI model predicts a final GPA of {predicted_gpa:.2f}. This student is at risk of academic probation."

        # Risk recommendation
        if risk_score < 0.3:
            recommendation = "No immediate intervention required. Continue monitoring standard progress."
        elif risk_score < 0.6:
            recommendation = f"Moderate risk detected (score: {risk_score:.0%}). A check-in meeting with an academic advisor is recommended."
        else:
            recommendation = f"🚨 High risk detected (score: {risk_score:.0%}). Priority intervention required — flag for counseling and academic support services."

        return f"{attendance_comment} {performance_comment} {gpa_comment} {recommendation}"

    @classmethod
    def analyze_record(cls, attendance_rate: float, assignments_avg: float, midterm_score: float, student_name: str = "Student"):
        """
        Full AI analysis: returns predicted GPA, risk score, and NLG insight.
        Returns a dict ready to store in AcademicRecord fields.
        """
        predicted_gpa = cls.predict_gpa(attendance_rate, assignments_avg, midterm_score)
        risk_score = cls.predict_risk_score(attendance_rate, assignments_avg, midterm_score)
        insight = cls.generate_insight(
            student_name, attendance_rate, assignments_avg,
            midterm_score, predicted_gpa, risk_score
        )
        return {
            "ai_predicted_gpa": predicted_gpa,
            "ai_risk_score": risk_score,
            "ai_insight": insight,
        }
