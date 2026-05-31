import os
import sqlite3

from werkzeug.security import generate_password_hash

_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'spendly.db')


def get_db():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            password   TEXT    NOT NULL,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT    NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount      REAL    NOT NULL CHECK (amount > 0),
            description TEXT,
            date        TEXT    NOT NULL DEFAULT (date('now')),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
        )
    """)

    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


def get_user_by_email(email):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def create_user(name, email, password_hash):
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, password_hash),
    )
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    for name in ["Food", "Travel", "Bills", "Shopping", "Health", "Entertainment"]:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))

    # INSERT OR IGNORE skips existing rows; a pre-existing plaintext password will NOT
    # be updated automatically — delete spendly.db and re-run to get the hashed version.
    cursor.execute(
        "INSERT OR IGNORE INTO users (name, email, password) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo1234")),
    )

    user = cursor.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)
    ).fetchone()
    food = cursor.execute(
        "SELECT id FROM categories WHERE name = ?", ("Food",)
    ).fetchone()
    travel = cursor.execute(
        "SELECT id FROM categories WHERE name = ?", ("Travel",)
    ).fetchone()

    if user and food and travel:
        for row in [
            (user["id"], food["id"],   450.00, "Lunch at canteen",  "2025-05-28"),
            (user["id"], travel["id"], 120.00, "Metro card top-up", "2025-05-27"),
            (user["id"], food["id"],    85.50, "Coffee and snacks", "2025-05-26"),
        ]:
            cursor.execute(
                "INSERT INTO expenses (user_id, category_id, amount, description, date)"
                " VALUES (?, ?, ?, ?, ?)",
                row,
            )

    conn.commit()
    conn.close()
