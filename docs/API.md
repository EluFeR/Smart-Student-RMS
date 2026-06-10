# Smart Student RMS — REST API Documentation

Base URL: `http://localhost:5000/api`

All endpoints require authentication (session cookie from `/auth/login`).

---

## Authentication

### POST /auth/login
```json
{ "email": "admin@school.edu", "password": "admin123" }
```

---

## Students

### GET /api/students
Returns all student records.

**Response:**
```json
[
  {
    "id": 1,
    "student_id": "STU-2024-0001",
    "full_name": "Alice Tadesse",
    "email": "alice@school.edu",
    "department": "Computer Science",
    "year_of_study": 2,
    "status": "active",
    "current_gpa": 3.42
  }
]
```

### GET /api/students/:id
Returns full student record including all academic records.

### POST /api/students
Create a new student.

**Request body:**
```json
{
  "student_id": "STU-2024-0099",
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@school.edu",
  "department": "Engineering",
  "program": "BSc Civil Engineering",
  "year_of_study": 1
}
```

### PUT /api/students/:id
Update student fields. Accepts partial body.

### DELETE /api/students/:id
Delete a student and all associated records.

---

## AI Prediction

### GET /api/students/:id/predict
Run AI analysis for a student given current-term data.

**Query Parameters:**
| Parameter | Type | Description |
|---|---|---|
| `attendance_rate` | float | 0.00 – 1.00 |
| `assignments_avg` | float | 0 – 100 |
| `midterm_score` | float | 0 – 100 |

**Example:**
```
GET /api/students/1/predict?attendance_rate=0.82&assignments_avg=74&midterm_score=68
```

**Response:**
```json
{
  "student_id": 1,
  "student_name": "Alice Tadesse",
  "input": { "attendance_rate": 0.82, "assignments_avg": 74.0, "midterm_score": 68.0 },
  "ai_predicted_gpa": 3.05,
  "ai_risk_score": 0.18,
  "ai_insight": "Alice has good attendance at 82%. Academic scores are satisfactory..."
}
```

---

## Analytics

### GET /api/analytics/summary
Returns full dashboard analytics.

**Response:**
```json
{
  "summary": {
    "total_students": 80,
    "active_students": 72,
    "at_risk_students": 8,
    "graduated": 0,
    "avg_gpa": 2.84,
    "avg_attendance": 76.3,
    "high_risk_count": 5
  },
  "gpa_distribution": { "0.0–1.0": 3, "1.0–2.0": 12, "2.0–3.0": 38, "3.0–3.5": 19, "3.5–4.0": 8 },
  "department_stats": [ { "department": "Computer Science", "count": 15, "avg_gpa": 3.1 } ],
  "risk_breakdown": { "low": 55, "moderate": 17, "high": 8 },
  "enrollment_trend": [ { "year": "2021", "count": 22 } ]
}
```
