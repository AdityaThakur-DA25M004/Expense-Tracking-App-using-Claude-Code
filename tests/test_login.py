import pytest
from database.db import seed_db

GENERIC_ERROR = b"Invalid email or password."


def _register(client, email="user@example.com", password="password123"):
    client.post("/register", data={"name": "Test User", "email": email, "password": password})


def _login(client, email="user@example.com", password="password123"):
    return client.post("/login", data={"email": email, "password": password})


def test_get_login_returns_200(client):
    rv = client.get("/login")
    assert rv.status_code == 200


def test_valid_login_sets_session_and_redirects(client):
    _register(client)
    rv = _login(client)
    assert rv.status_code == 302
    assert "/profile" in rv.headers["Location"]
    with client.session_transaction() as sess:
        assert "user_id" in sess
        assert isinstance(sess["user_id"], int)


def test_wrong_password_shows_error(client):
    _register(client)
    rv = _login(client, password="wrongpassword")
    assert rv.status_code == 200
    assert GENERIC_ERROR in rv.data


def test_unknown_email_shows_error(client):
    rv = _login(client, email="nobody@example.com")
    assert rv.status_code == 200
    assert GENERIC_ERROR in rv.data


def test_blank_email_shows_error(client):
    rv = client.post("/login", data={"email": "", "password": "password123"})
    assert rv.status_code == 200
    assert GENERIC_ERROR in rv.data


def test_blank_password_shows_error(client):
    rv = client.post("/login", data={"email": "user@example.com", "password": ""})
    assert rv.status_code == 200
    assert GENERIC_ERROR in rv.data


def test_no_session_after_failed_login(client):
    rv = _login(client, email="nobody@example.com")
    assert rv.status_code == 200
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_clears_session_and_redirects(client):
    _register(client)
    _login(client)
    rv = client.get("/logout")
    assert rv.status_code == 302
    assert rv.headers["Location"] in ("http://localhost/", "/")
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_logout_without_login_does_not_error(client):
    rv = client.get("/logout")
    assert rv.status_code == 302


def test_seed_demo_user_can_log_in(client):
    seed_db()
    rv = client.post("/login", data={"email": "demo@spendly.com", "password": "demo1234"})
    assert rv.status_code == 302
    assert "/profile" in rv.headers["Location"]
