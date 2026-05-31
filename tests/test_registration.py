import database.db as db_module
from werkzeug.security import check_password_hash


def post_register(client, name="Alice", email="alice@test.com", password="password123"):
    return client.post("/register", data={"name": name, "email": email, "password": password})


def test_get_register_returns_200(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_valid_registration_redirects(client):
    response = post_register(client)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_valid_registration_stores_hashed_password(client):
    plain = "password123"
    post_register(client, password=plain)
    conn = db_module.get_db()
    row = conn.execute("SELECT password FROM users WHERE email = ?", ("alice@test.com",)).fetchone()
    conn.close()
    assert row is not None
    assert row["password"] != plain
    assert check_password_hash(row["password"], plain)


def test_blank_name_shows_error(client):
    response = post_register(client, name="")
    assert response.status_code == 200
    assert b"All fields are required" in response.data


def test_blank_email_shows_error(client):
    response = post_register(client, email="")
    assert response.status_code == 200
    assert b"All fields are required" in response.data


def test_blank_password_shows_error(client):
    response = post_register(client, password="")
    assert response.status_code == 200
    assert b"All fields are required" in response.data


def test_short_password_shows_error(client):
    response = post_register(client, password="abc1234")
    assert response.status_code == 200
    assert b"at least 8 characters" in response.data


def test_duplicate_email_shows_error(client):
    post_register(client)
    response = post_register(client, name="Bob")
    assert response.status_code == 200
    assert b"already exists" in response.data


def test_no_insert_on_validation_failure(client):
    post_register(client, password="short")
    conn = db_module.get_db()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    assert count == 0
