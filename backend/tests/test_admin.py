from app.db.session import get_db
from app.main import app
from app.services.auth_service import bootstrap_admin
from tests.conftest import csrf_headers


def test_bootstrap_admin_and_analytics(client):
    gen = app.dependency_overrides[get_db]()
    session = next(gen)
    user = bootstrap_admin(session, "admin@campus.edu", "Secret123!", "Placement Admin")
    assert user.role.value == "admin"
    login = client.post("/api/v1/auth/login", json={"email": "admin@campus.edu", "password": "Secret123!"})
    assert login.status_code == 200, login.text
    analytics = client.get("/api/v1/admin/analytics")
    assert analytics.status_code == 200
    body = analytics.json()
    assert body["totals"]["users"] >= 1
    assert body["totals"]["jobs"] == 0
    assert body["totals"]["applications"] == 0
    users = client.get("/api/v1/admin/users")
    assert users.status_code == 200
    assert any(u["email"] == "admin@campus.edu" for u in users.json())
    second = client.post(
        "/api/v1/admin/users",
        headers=csrf_headers(client),
        json={"email": "a2@x.com", "password": "Secret123!"},
    )
    assert second.status_code in (404, 405, 422)


def test_second_bootstrap_rejected(db):
    bootstrap_admin(db, "admin2@campus.edu", "Secret123!", "A")
    from app.services.errors import Conflict

    try:
        bootstrap_admin(db, "admin3@campus.edu", "Secret123!", "B")
        raise AssertionError("expected conflict")
    except Conflict:
        pass
