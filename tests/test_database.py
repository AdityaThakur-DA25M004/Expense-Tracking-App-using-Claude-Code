import sqlite3
import pytest
import database.db as db_module
from database.db import init_db, seed_db


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def get_conn(app):
    return db_module.get_db()


# ------------------------------------------------------------------ #
# Table existence                                                     #
# ------------------------------------------------------------------ #

def test_users_table_exists(app):
    conn = get_conn(app)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    conn.close()
    assert row is not None


def test_categories_table_exists(app):
    conn = get_conn(app)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
    ).fetchone()
    conn.close()
    assert row is not None


def test_expenses_table_exists(app):
    conn = get_conn(app)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
    ).fetchone()
    conn.close()
    assert row is not None


# ------------------------------------------------------------------ #
# Column names                                                        #
# ------------------------------------------------------------------ #

def test_users_columns(app):
    conn = get_conn(app)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    conn.close()
    assert cols == {"id", "name", "email", "password", "created_at"}


def test_categories_columns(app):
    conn = get_conn(app)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(categories)").fetchall()}
    conn.close()
    assert cols == {"id", "name"}


def test_expenses_columns(app):
    conn = get_conn(app)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(expenses)").fetchall()}
    conn.close()
    assert cols == {"id", "user_id", "category_id", "amount", "description", "date", "created_at"}


# ------------------------------------------------------------------ #
# row_factory                                                         #
# ------------------------------------------------------------------ #

def test_row_factory_returns_dict_like_rows(app):
    conn = get_conn(app)
    conn.execute("INSERT INTO categories (name) VALUES (?)", ("TestCat",))
    conn.commit()
    row = conn.execute("SELECT * FROM categories WHERE name = 'TestCat'").fetchone()
    conn.close()
    assert row["name"] == "TestCat"


# ------------------------------------------------------------------ #
# Foreign key enforcement                                             #
# ------------------------------------------------------------------ #

def test_foreign_key_enforced_on_expenses(app):
    conn = get_conn(app)
    conn.execute("INSERT INTO categories (name) VALUES (?)", ("FK Test Cat",))
    conn.commit()
    cat = conn.execute("SELECT id FROM categories WHERE name = 'FK Test Cat'").fetchone()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)",
            (9999, cat["id"], 10.0, "2025-01-01"),
        )
        conn.commit()
    conn.close()


def test_fk_cascade_delete(app):
    conn = get_conn(app)
    conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        ("Cascade User", "cascade@test.com", "pass"),
    )
    conn.commit()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("cascade@test.com",)
    ).fetchone()
    conn.execute("INSERT INTO categories (name) VALUES (?)", ("Cascade Cat",))
    conn.commit()
    cat = conn.execute(
        "SELECT id FROM categories WHERE name = 'Cascade Cat'"
    ).fetchone()
    conn.execute(
        "INSERT INTO expenses (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)",
        (user["id"], cat["id"], 50.0, "2025-01-01"),
    )
    conn.commit()

    conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
    conn.commit()

    count = conn.execute(
        "SELECT count(*) FROM expenses WHERE user_id = ?", (user["id"],)
    ).fetchone()[0]
    conn.close()
    assert count == 0


# ------------------------------------------------------------------ #
# seed_db data presence                                               #
# ------------------------------------------------------------------ #

def test_seed_categories_populated(app):
    seed_db()
    conn = get_conn(app)
    count = conn.execute("SELECT count(*) FROM categories").fetchone()[0]
    conn.close()
    assert count >= 6


def test_seed_demo_user_exists(app):
    seed_db()
    conn = get_conn(app)
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["name"] == "Demo User"


def test_seed_expenses_exist(app):
    seed_db()
    conn = get_conn(app)
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()
    count = conn.execute(
        "SELECT count(*) FROM expenses WHERE user_id = ?", (user["id"],)
    ).fetchone()[0]
    conn.close()
    assert count >= 3


# ------------------------------------------------------------------ #
# Constraints                                                         #
# ------------------------------------------------------------------ #

def test_email_unique_constraint(app):
    conn = get_conn(app)
    conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        ("User A", "dup@test.com", "pass"),
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("User B", "dup@test.com", "pass"),
        )
        conn.commit()
    conn.close()


def test_amount_negative_check_constraint(app):
    conn = get_conn(app)
    conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        ("Check User", "check@test.com", "pass"),
    )
    conn.execute("INSERT INTO categories (name) VALUES (?)", ("Check Cat",))
    conn.commit()
    user = conn.execute(
        "SELECT id FROM users WHERE email = 'check@test.com'"
    ).fetchone()
    cat = conn.execute(
        "SELECT id FROM categories WHERE name = 'Check Cat'"
    ).fetchone()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)",
            (user["id"], cat["id"], -50.0, "2025-01-01"),
        )
        conn.commit()
    conn.close()


def test_amount_zero_check_constraint(app):
    conn = get_conn(app)
    conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        ("Zero User", "zero@test.com", "pass"),
    )
    conn.execute("INSERT INTO categories (name) VALUES (?)", ("Zero Cat",))
    conn.commit()
    user = conn.execute(
        "SELECT id FROM users WHERE email = 'zero@test.com'"
    ).fetchone()
    cat = conn.execute(
        "SELECT id FROM categories WHERE name = 'Zero Cat'"
    ).fetchone()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, category_id, amount, date) VALUES (?, ?, ?, ?)",
            (user["id"], cat["id"], 0.0, "2025-01-01"),
        )
        conn.commit()
    conn.close()


# ------------------------------------------------------------------ #
# Idempotency                                                         #
# ------------------------------------------------------------------ #

def test_init_db_idempotent(app):
    init_db()  # second call — should not raise
    init_db()


def test_seed_db_idempotent(app):
    seed_db()
    conn = get_conn(app)
    count_before = conn.execute("SELECT count(*) FROM categories").fetchone()[0]
    conn.close()

    seed_db()
    conn = get_conn(app)
    count_after = conn.execute("SELECT count(*) FROM categories").fetchone()[0]
    conn.close()

    assert count_before == count_after
