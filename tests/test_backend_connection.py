import database.db as db_module
import database.queries as queries
from werkzeug.security import generate_password_hash


# ── Helpers ────────────────────────────────────────────────────────────────


def _insert_user(conn, name="Test User", email="test@example.com", password="hashed"):
    cur = conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, generate_password_hash(password)),
    )
    conn.commit()
    return cur.lastrowid


def _insert_category(conn, name):
    cur = conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    return conn.execute("SELECT id FROM categories WHERE name = ?", (name,)).fetchone()["id"]


def _insert_expense(conn, user_id, cat_id, amount, date, description="expense"):
    conn.execute(
        "INSERT INTO expenses (user_id, category_id, amount, description, date)"
        " VALUES (?, ?, ?, ?, ?)",
        (user_id, cat_id, amount, description, date),
    )
    conn.commit()


# ── get_user_by_id ─────────────────────────────────────────────────────────


def test_get_user_by_id_returns_none_for_missing(app):
    assert queries.get_user_by_id(9999) is None


def test_get_user_by_id_returns_name_and_email(app):
    conn = db_module.get_db()
    uid = _insert_user(conn, name="Alice Bob", email="alice@example.com")
    conn.close()

    result = queries.get_user_by_id(uid)
    assert result["name"] == "Alice Bob"
    assert result["email"] == "alice@example.com"


def test_get_user_by_id_member_since_format(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    conn.close()

    result = queries.get_user_by_id(uid)
    # Should be "Month YYYY" format, e.g. "May 2026"
    parts = result["member_since"].split()
    assert len(parts) == 2
    assert parts[1].isdigit() and len(parts[1]) == 4


# ── get_summary_stats ──────────────────────────────────────────────────────


def test_get_summary_stats_zero_expenses(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    conn.close()

    stats = queries.get_summary_stats(uid)
    assert stats["total_spent"] == 0.0
    assert stats["tx_count"] == 0
    assert stats["top_category"] == "—"


def test_get_summary_stats_totals(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    _insert_expense(conn, uid, food_id, 100.0, "2025-01-01")
    _insert_expense(conn, uid, food_id, 200.0, "2025-01-02")
    conn.close()

    stats = queries.get_summary_stats(uid)
    assert stats["total_spent"] == 300.0
    assert stats["tx_count"] == 2


def test_get_summary_stats_top_category(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    bills_id = _insert_category(conn, "Bills")
    _insert_expense(conn, uid, food_id, 50.0, "2025-01-01")
    _insert_expense(conn, uid, bills_id, 500.0, "2025-01-02")
    conn.close()

    stats = queries.get_summary_stats(uid)
    assert stats["top_category"] == "Bills"


# ── get_recent_transactions ────────────────────────────────────────────────


def test_get_recent_transactions_empty(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    conn.close()

    assert queries.get_recent_transactions(uid) == []


def test_get_recent_transactions_fields(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    _insert_expense(conn, uid, food_id, 75.0, "2025-05-28", "Lunch")
    conn.close()

    txns = queries.get_recent_transactions(uid)
    assert len(txns) == 1
    assert txns[0]["description"] == "Lunch"
    assert txns[0]["category"] == "Food"
    assert txns[0]["amount"] == 75.0


def test_get_recent_transactions_date_format(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    _insert_expense(conn, uid, food_id, 10.0, "2025-05-28")
    conn.close()

    txns = queries.get_recent_transactions(uid)
    assert txns[0]["date"] == "28 May 2025"


def test_get_recent_transactions_ordered_newest_first(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    _insert_expense(conn, uid, food_id, 10.0, "2025-01-01", "Older")
    _insert_expense(conn, uid, food_id, 20.0, "2025-03-01", "Newer")
    conn.close()

    txns = queries.get_recent_transactions(uid)
    assert txns[0]["description"] == "Newer"
    assert txns[1]["description"] == "Older"


def test_get_recent_transactions_limit(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    for i in range(15):
        _insert_expense(conn, uid, food_id, float(i + 1), f"2025-01-{i + 1:02d}")
    conn.close()

    assert len(queries.get_recent_transactions(uid, limit=5)) == 5
    assert len(queries.get_recent_transactions(uid)) == 10  # default limit


# ── get_category_breakdown ─────────────────────────────────────────────────


def test_get_category_breakdown_empty(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    conn.close()

    assert queries.get_category_breakdown(uid) == []


def test_get_category_breakdown_fields(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    _insert_expense(conn, uid, food_id, 100.0, "2025-01-01")
    conn.close()

    breakdown = queries.get_category_breakdown(uid)
    assert len(breakdown) == 1
    assert breakdown[0]["name"] == "Food"
    assert breakdown[0]["total"] == 100.0
    assert breakdown[0]["pct"] == 100


def test_get_category_breakdown_pct_sums_to_100(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    travel_id = _insert_category(conn, "Travel")
    bills_id = _insert_category(conn, "Bills")
    _insert_expense(conn, uid, food_id, 200.0, "2025-01-01")
    _insert_expense(conn, uid, travel_id, 150.0, "2025-01-02")
    _insert_expense(conn, uid, bills_id, 50.0, "2025-01-03")
    conn.close()

    breakdown = queries.get_category_breakdown(uid)
    assert sum(c["pct"] for c in breakdown) == 100


def test_get_category_breakdown_rounding_remainder_to_largest(app):
    """3 equal categories: raw 33.33 each, floor gives 33+33+33=99, remainder goes to first."""
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    travel_id = _insert_category(conn, "Travel")
    bills_id = _insert_category(conn, "Bills")
    for cat_id in (food_id, travel_id, bills_id):
        _insert_expense(conn, uid, cat_id, 1.0, "2025-01-01")
    conn.close()

    breakdown = queries.get_category_breakdown(uid)
    pcts = [c["pct"] for c in breakdown]
    assert sum(pcts) == 100
    assert pcts[0] == 34  # largest absorbs remainder


def test_get_category_breakdown_ordered_by_total_desc(app):
    conn = db_module.get_db()
    uid = _insert_user(conn)
    food_id = _insert_category(conn, "Food")
    bills_id = _insert_category(conn, "Bills")
    _insert_expense(conn, uid, food_id, 50.0, "2025-01-01")
    _insert_expense(conn, uid, bills_id, 200.0, "2025-01-02")
    conn.close()

    breakdown = queries.get_category_breakdown(uid)
    assert breakdown[0]["name"] == "Bills"
    assert breakdown[1]["name"] == "Food"


# ── /profile route integration ─────────────────────────────────────────────


def test_profile_redirects_unauthenticated(client):
    rv = client.get("/profile")
    assert rv.status_code == 302
    assert "/login" in rv.headers["Location"]


def _register_and_login(client, name, email, password):
    client.post("/register", data={"name": name, "email": email, "password": password})
    client.post("/login", data={"email": email, "password": password})


def test_profile_shows_real_user_data(client):
    _register_and_login(client, "Jane Doe", "jane@example.com", "password1")

    rv = client.get("/profile")
    assert rv.status_code == 200
    assert b"Jane Doe" in rv.data
    assert b"jane@example.com" in rv.data


def test_profile_shows_inr_symbol(client, app):
    _register_and_login(client, "Raj Kumar", "raj@example.com", "password1")

    conn = db_module.get_db()
    uid = conn.execute("SELECT id FROM users WHERE email = ?", ("raj@example.com",)).fetchone()["id"]
    food_id = _insert_category(conn, "Food")
    _insert_expense(conn, uid, food_id, 500.0, "2025-06-01")
    conn.close()

    rv = client.get("/profile")
    assert rv.status_code == 200
    assert "₹500.00".encode() in rv.data


def test_profile_zero_expense_user_renders_without_error(client):
    _register_and_login(client, "New User", "new@example.com", "password1")

    rv = client.get("/profile")
    assert rv.status_code == 200
    assert "₹0.00".encode() in rv.data


def test_profile_shows_correct_total_spent(client):
    _register_and_login(client, "Budget User", "budget@example.com", "password1")

    conn = db_module.get_db()
    uid = conn.execute("SELECT id FROM users WHERE email = ?", ("budget@example.com",)).fetchone()["id"]
    food_id = _insert_category(conn, "Food")
    _insert_expense(conn, uid, food_id, 100.0, "2025-06-01")
    _insert_expense(conn, uid, food_id, 250.0, "2025-06-02")
    conn.close()

    rv = client.get("/profile")
    assert "₹350.00".encode() in rv.data
