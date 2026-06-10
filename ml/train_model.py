"""
ML Model Training Script
========================
Trains two models:
  1. GPA Predictor     — Random Forest Regressor
  2. At-Risk Classifier — Gradient Boosting Classifier

Run: python ml/train_model.py
Models saved to ml/models/
"""

import os
import numpy as np
import pandas as pd
import joblib
import logging
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

np.random.seed(42)


def generate_synthetic_data(n_samples=2500):
    """
    Generate realistic synthetic student data for training.
    Features: attendance_rate, assignments_avg, midterm_score, study_index
    Targets:  final_gpa (regression), at_risk (classification)
    """
    logger.info(f"Generating {n_samples} synthetic student records...")

    attendance = np.random.beta(7, 2, n_samples)                    # skewed high (realistic)
    assignments = np.random.normal(68, 15, n_samples).clip(0, 100)
    midterm = np.random.normal(65, 18, n_samples).clip(0, 100)

    # Add correlations
    assignments += (attendance - 0.75) * 20
    assignments = assignments.clip(0, 100)
    midterm += (attendance - 0.75) * 15
    midterm = midterm.clip(0, 100)

    # Derived feature
    study_index = (assignments * 0.4 + midterm * 0.6)

    # GPA: weighted formula + noise
    raw_gpa = (
        attendance * 0.20 * 4.0 +
        (assignments / 100) * 0.30 * 4.0 +
        (midterm / 100) * 0.50 * 4.0 +
        np.random.normal(0, 0.15, n_samples)
    )
    final_gpa = np.clip(raw_gpa, 0.0, 4.0)

    # At-risk: 1 if GPA < 2.0 or attendance < 0.6
    at_risk = ((final_gpa < 2.0) | (attendance < 0.6)).astype(int)

    df = pd.DataFrame({
        "attendance_pct": attendance * 100,
        "assignments_avg": assignments,
        "midterm_score": midterm,
        "study_index": study_index,
        "final_gpa": final_gpa,
        "at_risk": at_risk,
    })

    csv_path = os.path.join(DATA_DIR, "synthetic_student_data.csv")
    df.to_csv(csv_path, index=False)
    logger.info(f"Dataset saved to {csv_path}")
    logger.info(f"At-risk rate: {at_risk.mean():.1%}")
    return df


def train_gpa_predictor(df):
    """Train Random Forest Regressor to predict final GPA."""
    logger.info("Training GPA Predictor (Random Forest Regressor)...")
    features = ["attendance_pct", "assignments_avg", "midterm_score", "study_index"]
    X = df[features].values
    y = df["final_gpa"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
        )),
    ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")

    logger.info(f"GPA Predictor — MSE: {mse:.4f}, R²: {r2:.4f}, CV R²: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    path = os.path.join(MODEL_DIR, "gpa_predictor.pkl")
    joblib.dump(model, path)
    logger.info(f"GPA predictor saved to {path}")
    return model, {"mse": mse, "r2": r2, "cv_r2_mean": cv_scores.mean()}


def train_risk_classifier(df):
    """Train Gradient Boosting Classifier for at-risk detection."""
    logger.info("Training At-Risk Classifier (Gradient Boosting)...")
    features = ["attendance_pct", "assignments_avg", "midterm_score", "study_index"]
    X = df[features].values
    y = df["at_risk"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("gb", GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=4,
            random_state=42,
        )),
    ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["Not At Risk", "At Risk"])
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")

    logger.info(f"Risk Classifier — Accuracy: {acc:.4f}, CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    logger.info(f"\n{report}")

    path = os.path.join(MODEL_DIR, "risk_classifier.pkl")
    joblib.dump(model, path)
    logger.info(f"Risk classifier saved to {path}")
    return model, {"accuracy": acc, "cv_accuracy_mean": cv_scores.mean()}


def main():
    logger.info("=" * 60)
    logger.info("Smart Student RMS — ML Model Training")
    logger.info("=" * 60)

    df = generate_synthetic_data(n_samples=2500)

    gpa_model, gpa_metrics = train_gpa_predictor(df)
    risk_model, risk_metrics = train_risk_classifier(df)

    logger.info("\n" + "=" * 60)
    logger.info("Training Complete — Summary")
    logger.info("=" * 60)
    logger.info(f"GPA Predictor  — R²: {gpa_metrics['r2']:.4f}")
    logger.info(f"Risk Classifier — Accuracy: {risk_metrics['accuracy']:.4f}")
    logger.info("Models saved in ml/models/")


if __name__ == "__main__":
    main()
