# 🎓 Smart Student Record Management System with AI Insights

A full-stack intelligent student management system that combines traditional academic
record-keeping with machine learning to predict student performance, detect at-risk
students, and generate actionable insights — with separate portals for academic staff
and students.

🔗 **Live demo:** _add your Render URL here after deploying_

---

## ✨ What it does

**Two sides, one system:**

- **Staff side** — admins and lecturers log in to manage students, enter grades &
  attendance, and view an analytics dashboard. When a grade record is added, the AI
  automatically predicts the final GPA, scores dropout risk, and writes a plain-English
  insight — flagging at-risk students automatically.
- **Student side** — students sign up with the Student ID & email the academic office
  registered for them. The system **approves the account only if a matching staff-created
  record exists**, then gives them a read-only dashboard of their own grades, attendance,
  and feedback.

Both staff and students log in through the **same login page** — the system routes each
user to the correct dashboard automatically based on their account type.

---

## 🚀 Features

- **Student CRUD Management** — add, update, view, and archive student records
- **Student Self-Service Portal** — sign up, auto-approval against school records, view own grades
- **AI Performance Prediction** — predicts end-of-term GPA from attendance, assignments & midterm
- **At-Risk Detection** — automatically flags students likely to fail or drop out
- **Smart Analytics Dashboard** — charts for grade distribution, trends & department comparisons
- **AI Insight Reports** — auto-generated natural-language summaries per student
- **Role-Based Access** — admin, lecturer, and student roles
- **REST API** — full JSON API for integration with other systems
- **PDF Reports** — downloadable per-student academic reports

---

## 🧠 AI/ML Components

| Component | Description | Algorithm |
|---|---|---|
| Performance Predictor | Predicts final GPA | Random Forest Regressor |
| At-Risk Classifier | Flags at-risk students | Gradient Boosting Classifier |
| Insight Generator | Plain-English summaries per student | Rule-based NLG + templates |

> Models are pre-trained on synthetic data and shipped as `.pkl` files, so predictions
> work out of the box. The app falls back to a heuristic formula if the models are missing.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, Flask, SQLAlchemy
- **ML:** scikit-learn, pandas, numpy, joblib
- **Frontend:** HTML5, Bootstrap 5, Chart.js
- **Database:** SQLite (dev) / PostgreSQL (production)
- **Auth:** Flask-Login, Werkzeug password hashing
- **Reports:** ReportLab (PDF)
- **Server:** Gunicorn (production WSGI)

---

## ⚡ Quick Start (Local)

```bash
# 1. Clone & set up environment
git clone https://github.com/EluFeR/Smart-Student-RMS.git
cd Smart-Student-RMS
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

# 2. (Optional) configure environment
cp .env.example .env

# 3. Seed the database with demo data
python scripts/seed_db.py

# 4. (Optional) retrain the ML models
python ml/train_model.py

# 5. Run
python run.py
```

Visit **http://localhost:5000**

**Default logins:**
| Role | Email | Password |
|---|---|---|
| Admin | `admin@school.edu` | `admin123` |
| Lecturer | `alice@school.edu` | `lecturer123` |

> Students don't have default logins — they sign up via the portal using a seeded
> student's ID and email (open any student as staff to find valid credentials).

---

## 👥 How accounts work

| | Staff (admin / lecturer) | Students |
|---|---|---|
| **Created by** | An admin via **Manage Users** | They sign up themselves |
| **Approval** | Active immediately | Auto-approved only if staff already added a matching record |
| **Access** | Manage students, grades, analytics | Read-only view of their own record |

---

## ☁️ Deployment (Render)

This repo is deploy-ready for [Render](https://render.com) via `render.yaml`.

1. Push the repo to GitHub.
2. On Render: **New → Blueprint** → select this repo → **Apply**.
3. Render provisions a PostgreSQL database, installs dependencies, seeds data, and starts
   Gunicorn automatically.

`SECRET_KEY` is auto-generated and `DATABASE_URL` is injected by Render — no manual config
needed. **After your first deploy, log in and change the default admin password.**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/students` | List all students |
| GET | `/api/students/<id>` | Get student details |
| POST | `/api/students` | Create student |
| PUT | `/api/students/<id>` | Update student |
| DELETE | `/api/students/<id>` | Delete student |
| GET | `/api/students/<id>/predict` | AI performance prediction |
| GET | `/api/analytics/summary` | Dashboard analytics |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📄 License

MIT License — free to use, modify, and distribute.
