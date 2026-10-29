from app.security.auth import hash_password, verify_password
from tests.conftest import csrf_headers


def test_password_hashing_not_plaintext():
    hashed = hash_password("Secret123!")
    assert hashed != "Secret123!"
    assert hashed.startswith("$argon2")
    assert verify_password("Secret123!", hashed)
    assert not verify_password("wrong", hashed)


def test_student_register_and_login(client):
    r = client.post(
        "/api/v1/auth/register/student",
        json={
            "email": "stu@campus.edu",
            "password": "Secret123!",
            "full_name": "Ada Student",
            "department": "CSE",
            "degree": "B.Tech",
            "graduation_year": 2026,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "student"
    assert "access_token" in r.cookies
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "stu@campus.edu"
    client.post("/api/v1/auth/logout", headers=csrf_headers(client))
    r2 = client.post("/api/v1/auth/login", json={"email": "stu@campus.edu", "password": "Secret123!"})
    assert r2.status_code == 200


def test_recruiter_register(client):
    r = client.post(
        "/api/v1/auth/register/recruiter",
        json={
            "email": "rec@company.com",
            "password": "Secret123!",
            "full_name": "Ravi Recruiter",
            "company_name": "Northwind",
        },
    )
    assert r.status_code == 200
    assert r.json()["role"] == "recruiter"


def test_no_public_admin_register(client):
    r = client.post("/api/v1/auth/register/admin", json={"email": "a@x.com", "password": "Secret123!"})
    assert r.status_code in (404, 405, 422)


def test_bad_login(client):
    r = client.post("/api/v1/auth/login", json={"email": "nobody@x.com", "password": "nope"})
    assert r.status_code == 401


def test_health_endpoints(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    ready = client.get("/api/v1/health/ready")
    assert ready.status_code in (200, 503)
    assert "database" in ready.json()
