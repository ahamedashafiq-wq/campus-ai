import pytest
from tests.conftest import csrf_headers


def test_resume_upload_and_skill_extract(client):
    fitz = pytest.importorskip("fitz")
    client.post(
        "/api/v1/auth/register/student",
        json={"email": "cv@campus.edu", "password": "Secret123!", "full_name": "CV Student", "department": "CSE"},
    )
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Jane Doe\nSkills: Python, FastAPI, PostgreSQL, Docker, React\nProjects: CampusMatch API")
    data = doc.tobytes()
    doc.close()
    r = client.post(
        "/api/v1/resumes",
        headers=csrf_headers(client),
        files={"file": ("resume.pdf", data, "application/pdf")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] in ("processed", "no_text")
    assert body["extraction"] is not None
    skills = {s["slug"] for s in body["extraction"]["extracted_skills"]}
    assert "python" in skills
    listed = client.get("/api/v1/resumes")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
