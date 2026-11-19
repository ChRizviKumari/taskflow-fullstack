from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "SECRET_KEY": "test-secret",
        "PBKDF2_ITERATIONS": 1000,  # fast hashing for tests only
    })


@pytest.fixture()
def client(app):
    return app.test_client()


class Auth:
    def __init__(self, client, token: str, user: dict):
        self.client, self.token, self.user = client, token, user

    @property
    def h(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, url, **kw):
        return self.client.get(url, headers=self.h, **kw)

    def post(self, url, json=None):
        return self.client.post(url, json=json, headers=self.h)

    def patch(self, url, json=None):
        return self.client.patch(url, json=json, headers=self.h)

    def delete(self, url):
        return self.client.delete(url, headers=self.h)


def make_user(client, email="alice@example.com", name="Alice") -> Auth:
    r = client.post("/api/auth/register", json={"email": email, "name": name, "password": "correct-horse"})
    assert r.status_code == 201, r.get_json()
    body = r.get_json()
    return Auth(client, body["token"], body["user"])


@pytest.fixture()
def alice(client) -> Auth:
    return make_user(client)


@pytest.fixture()
def bob(client) -> Auth:
    return make_user(client, "bob@example.com", "Bob")


@pytest.fixture()
def board(alice):
    r = alice.post("/api/boards", {"name": "Sprint"})
    assert r.status_code == 201
    return r.get_json()["board"]


def add_task(auth: Auth, column_id: int, title: str = "T", **extra) -> dict:
    r = auth.post(f"/api/columns/{column_id}/tasks", {"title": title, **extra})
    assert r.status_code == 201, r.get_json()
    return r.get_json()["task"]
