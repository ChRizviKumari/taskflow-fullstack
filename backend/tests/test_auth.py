import time

from app.security import issue_token


def test_register_returns_user_and_token(client):
    r = client.post("/api/auth/register", json={"email": "A@Example.com", "name": "A", "password": "longenough1"})
    assert r.status_code == 201
    body = r.get_json()
    assert body["user"]["email"] == "a@example.com"
    assert "password_hash" not in body["user"]
    assert body["token"].count(".") == 2


def test_register_duplicate_email_conflicts(client, alice):
    r = client.post("/api/auth/register", json={"email": "ALICE@example.com", "name": "x", "password": "longenough1"})
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "email_taken"


def test_register_validation_errors_are_structured(client):
    r = client.post("/api/auth/register", json={"email": "nope", "name": "", "password": "short"})
    assert r.status_code == 422
    err = r.get_json()["error"]
    assert err["code"] == "validation_error"
    assert {d["field"] for d in err["details"]} == {"email", "name", "password"}


def test_register_rejects_unknown_fields_and_non_object(client):
    r = client.post("/api/auth/register", json={"email": "a@b.co", "name": "a", "password": "longenough1", "admin": True})
    assert r.status_code == 422
    assert client.post("/api/auth/register", json=[1, 2]).status_code == 400


def test_login_success_and_failure(client, alice):
    ok = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "correct-horse"})
    assert ok.status_code == 200 and ok.get_json()["token"]
    bad = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "wrong"})
    unknown = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "wrong"})
    assert bad.status_code == unknown.status_code == 401
    assert bad.get_json() == unknown.get_json()


def test_me_requires_valid_token(client, alice):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401
    r = alice.get("/api/auth/me")
    assert r.status_code == 200 and r.get_json()["user"]["name"] == "Alice"


def test_expired_token_rejected(client):
    token = issue_token(1, "test-secret", 5, now=time.time() - 60)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert "expired" in r.get_json()["error"]["message"]


def test_unknown_route_uses_error_envelope(client):
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_stored_password_is_hashed(app, alice):
    import sqlite3
    row = sqlite3.connect(app.config["DATABASE"]).execute("SELECT password_hash FROM users").fetchone()
    assert row[0].startswith("pbkdf2_sha256$") and "correct-horse" not in row[0]
