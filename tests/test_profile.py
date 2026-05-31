import pytest


def _register_and_login(client, name="Test User", email="user@example.com", password="password123"):
    client.post("/register", data={"name": name, "email": email, "password": password})
    client.post("/login", data={"email": email, "password": password})


def test_profile_redirects_when_not_logged_in(client):
    rv = client.get("/profile")
    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]


def test_profile_returns_200_when_logged_in(client):
    _register_and_login(client)
    rv = client.get("/profile")
    assert rv.status_code == 200


def test_profile_shows_name(client):
    _register_and_login(client, name="Alice")
    rv = client.get("/profile")
    assert b"Alice" in rv.data


def test_profile_shows_email(client):
    _register_and_login(client, email="alice@example.com")
    rv = client.get("/profile")
    assert b"alice@example.com" in rv.data


def test_profile_shows_member_since(client):
    _register_and_login(client)
    rv = client.get("/profile")
    assert b"Member since" in rv.data


def test_profile_not_accessible_after_logout(client):
    _register_and_login(client)
    client.get("/logout")
    rv = client.get("/profile")
    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]
