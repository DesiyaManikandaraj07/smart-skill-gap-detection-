"""API and pipeline smoke tests."""

from __future__ import annotations

import io

import fitz
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


SAMPLE_RESUME = """
Jane Student
Bangalore, India
jane@email.com

Skills
Python, JavaScript, React, SQL, Git, Docker

Education
B.Tech Computer Science, Example University, 2025
CGPA: 3.6/4.0

Projects
- Built a React dashboard for campus events
- Python FastAPI service for notes

Experience
Software Intern at StartupCo (2024 – present)
1.5 years of experience building web apps

Certifications
AWS Cloud Practitioner
"""


LOW_GPA_RESUME = """
Low Gpa Candidate
Location: Remote

Skills
Python, Machine Learning, PyTorch, SQL, Docker, Git, Pandas, NumPy, scikit-learn, Amazon Web Services

Education
B.Tech Computer Science
CGPA: 2.1/4.0

Projects
- Deep learning image classifier
- End-to-end ML API

Experience
2.5 years of experience in ML engineering
"""


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_register_login_me():
    import uuid

    email = f"tester-{uuid.uuid4().hex[:8]}@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Test User"},
    )
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_list_roles():
    res = client.get("/api/v1/roles")
    assert res.status_code == 200
    assert len(res.json()) >= 5


def test_job_feed_all_levels():
    res = client.get("/api/v1/jobs/feed?level=all&source=curated")
    assert res.status_code == 200
    jobs = res.json()
    assert len(jobs) >= 10
    levels = {j["experience_level"] for j in jobs}
    assert {"entry", "mid", "senior"} <= levels
    detail = client.get(f"/api/v1/jobs/{jobs[0]['id']}")
    assert detail.status_code == 200
    assert detail.json()["description"]


def test_job_feed_entry_filter():
    res = client.get("/api/v1/jobs/feed?level=entry&source=curated")
    assert res.status_code == 200
    jobs = res.json()
    assert jobs
    assert all(j["experience_level"] == "entry" for j in jobs)


def test_analyze_resume():
    pdf = _make_pdf(SAMPLE_RESUME)
    res = client.post(
        "/api/v1/analyze",
        data={
            "name": "Jane Student",
            "extra_skills": "TypeScript",
            "role_id": "frontend-engineer",
            "job_description": "",
            "location": "Bangalore",
            "cgpa": "3.6",
        },
        files={"file": ("resume.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert 0 <= body["selection_likelihood_pct"] <= 100
    assert "summary" in body and body["summary"]["strengths"]
    assert "required_skills" in body
    assert "effective_selection_pct" in body


def test_hard_gate_cgpa_blocks_effective_score():
    pdf = _make_pdf(LOW_GPA_RESUME)
    res = client.post(
        "/api/v1/analyze",
        data={
            "name": "Low Gpa",
            "role_id": "ml-engineer",
            "location": "Bangalore",
            "cgpa": "2.1",
        },
        files={"file": ("resume.pdf", io.BytesIO(pdf), "application/pdf")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["eligible"] is False
    assert body["effective_selection_pct"] == 0.0
    assert body["summary"]["critical_blockers"]


def test_what_if():
    res = client.post(
        "/api/v1/what-if",
        json={
            "candidate_name": "Jane",
            "current_skills": ["JavaScript", "React"],
            "add_skills": ["TypeScript", "Docker"],
            "job_skills": ["JavaScript", "TypeScript", "React", "Docker", "HTML"],
            "experience_years": 1,
            "project_count": 2,
            "cert_count": 1,
            "has_degree": True,
            "eligible": True,
        },
    )
    assert res.status_code == 200
    assert res.json()["delta_pct"] >= 0
