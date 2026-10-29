from tests.conftest import csrf_headers


def _register_pair(client):
    s = client.post(
        "/api/v1/auth/register/student",
        json={
            "email": "s1@campus.edu",
            "password": "Secret123!",
            "full_name": "Student One",
            "department": "CSE",
            "graduation_year": 2026,
        },
    )
    assert s.status_code == 200, s.text
    student_cookies = dict(client.cookies)
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    r = client.post(
        "/api/v1/auth/register/recruiter",
        json={
            "email": "r1@co.com",
            "password": "Secret123!",
            "full_name": "Recruiter One",
            "company_name": "Acme",
        },
    )
    assert r.status_code == 200, r.text
    return student_cookies


def test_job_create_publish_and_ownership(client):
    _register_pair(client)
    created = client.post(
        "/api/v1/jobs",
        headers=csrf_headers(client),
        json={
            "title": "Backend Engineer",
            "description": "Work on APIs and data pipelines for campus hiring.",
            "required_skills": ["Python", "SQL"],
            "preferred_skills": ["Docker"],
        },
    )
    assert created.status_code == 200, created.text
    job_id = created.json()["id"]
    pub = client.post(f"/api/v1/jobs/{job_id}/publish", headers=csrf_headers(client))
    assert pub.status_code == 200
    assert pub.json()["status"] == "published"
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    client.post(
        "/api/v1/auth/register/recruiter",
        json={"email": "other@co.com", "password": "Secret123!", "full_name": "Other", "company_name": "OtherCo"},
    )
    steal = client.patch(
        f"/api/v1/jobs/{job_id}",
        headers=csrf_headers(client),
        json={"title": "Hacked"},
    )
    assert steal.status_code == 403


def test_application_duplicate_and_transitions(client):
    _register_pair(client)
    created = client.post(
        "/api/v1/jobs",
        headers=csrf_headers(client),
        json={
            "title": "Data Analyst",
            "description": "Analyze placement outcomes using SQL and Python reporting.",
            "required_skills": ["SQL", "Python"],
        },
    )
    job_id = created.json()["id"]
    client.post(f"/api/v1/jobs/{job_id}/publish", headers=csrf_headers(client))
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    client.post("/api/v1/auth/login", json={"email": "s1@campus.edu", "password": "Secret123!"})
    a1 = client.post("/api/v1/applications", headers=csrf_headers(client), json={"job_id": job_id})
    assert a1.status_code == 200, a1.text
    a2 = client.post("/api/v1/applications", headers=csrf_headers(client), json={"job_id": job_id})
    assert a2.status_code == 409
    app_id = a1.json()["id"]
    bad = client.post(
        f"/api/v1/applications/{app_id}/status",
        headers=csrf_headers(client),
        json={"status": "shortlisted"},
    )
    assert bad.status_code == 403
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    client.post("/api/v1/auth/login", json={"email": "r1@co.com", "password": "Secret123!"})
    ok = client.post(
        f"/api/v1/applications/{app_id}/status",
        headers=csrf_headers(client),
        json={"status": "under_review"},
    )
    assert ok.status_code == 200
    invalid = client.post(
        f"/api/v1/applications/{app_id}/status",
        headers=csrf_headers(client),
        json={"status": "selected"},
    )
    assert invalid.status_code == 400
    short = client.post(
        f"/api/v1/applications/{app_id}/status",
        headers=csrf_headers(client),
        json={"status": "shortlisted"},
    )
    assert short.status_code == 200
    interview = client.post(
        "/api/v1/interviews",
        headers=csrf_headers(client),
        json={"application_id": app_id, "scheduled_at": "2026-11-01T10:00:00Z", "location_or_link": "https://meet.example"},
    )
    assert interview.status_code == 200, interview.text


def test_admin_forbidden_for_student(client):
    client.post(
        "/api/v1/auth/register/student",
        json={"email": "s2@campus.edu", "password": "Secret123!", "full_name": "S Two"},
    )
    r = client.get("/api/v1/admin/analytics")
    assert r.status_code == 403
