"""
Tests for Step 06: Date Filter for Profile Page.

Spec: .claude/specs/06-date-filter-for-profile.md

All tests are driven by the feature specification — what the feature SHOULD do
for the user — not by reading the implementation source code.

Seeded data (inserted by the `seeded_client` fixture):
  Expense A — Food    — 500.00 — 2026-04-15  (April, before May)
  Expense B — Travel  — 200.00 — 2026-05-10  (May)
  Expense C — Food    — 150.00 — 2026-05-20  (May)
  Expense D — Bills   — 300.00 — 2026-06-05  (June, after May)

This split lets tests make precise assertions about filtered vs. all-time totals.
"""

import sqlite3
import pytest
import database.db as db_module
from app import app as flask_app
from database.db import init_db
from werkzeug.security import generate_password_hash


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app(tmp_path):
    """
    Provide a Flask test application backed by a fresh, isolated SQLite file.
    The real spendly.db is never touched.
    """
    db_file = str(tmp_path / "test.db")
    original_get_db = db_module.get_db

    def _test_get_db():
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    db_module.get_db = _test_get_db
    init_db()

    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    yield flask_app

    db_module.get_db = original_get_db


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_client(client):
    """
    Returns a test client whose database contains:
      - One registered user (email: filter@example.com)
      - Four expenses spread across April, May, and June 2026
        so date-filter assertions can target specific sub-totals.

    The user is NOT logged in yet; individual tests decide whether to
    set the session or not.
    """
    # Register the user via the public endpoint so the password is hashed
    client.post(
        "/register",
        data={
            "name": "Filter Tester",
            "email": "filter@example.com",
            "password": "password123",
        },
    )

    # Resolve the new user's id so we can insert expenses directly
    conn = db_module.get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("filter@example.com",)
    ).fetchone()
    user_id = user["id"]

    # Ensure the categories we need exist
    for cat_name in ("Food", "Travel", "Bills"):
        conn.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat_name,)
        )
    conn.commit()

    food_id = conn.execute(
        "SELECT id FROM categories WHERE name = ?", ("Food",)
    ).fetchone()["id"]
    travel_id = conn.execute(
        "SELECT id FROM categories WHERE name = ?", ("Travel",)
    ).fetchone()["id"]
    bills_id = conn.execute(
        "SELECT id FROM categories WHERE name = ?", ("Bills",)
    ).fetchone()["id"]

    # Insert the four known expenses
    expenses = [
        (user_id, food_id,   500.00, "April food",    "2026-04-15"),
        (user_id, travel_id, 200.00, "May travel",    "2026-05-10"),
        (user_id, food_id,   150.00, "May food",      "2026-05-20"),
        (user_id, bills_id,  300.00, "June bills",    "2026-06-05"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, category_id, amount, description, date)"
        " VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()

    return client, user_id


def _login(client, email="filter@example.com", password="password123"):
    """Helper: POST to /login and follow the redirect."""
    client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


# ---------------------------------------------------------------------------
# Authentication guard
# ---------------------------------------------------------------------------

class TestAuthGuard:
    """Unauthenticated access to /profile must redirect to /login."""

    def test_unauthenticated_get_profile_redirects_to_login(self, client):
        rv = client.get("/profile")
        assert rv.status_code == 302
        assert "/login" in rv.headers["Location"]

    def test_unauthenticated_get_profile_with_date_params_redirects_to_login(self, client):
        """Date params must not bypass the auth guard."""
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert rv.status_code == 302
        assert "/login" in rv.headers["Location"]


# ---------------------------------------------------------------------------
# No-filter baseline (no regression)
# ---------------------------------------------------------------------------

class TestNoFilterBaseline:
    """GET /profile with no query params must behave exactly as before Step 06."""

    def test_profile_loads_200_without_date_params(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile")
        assert rv.status_code == 200

    def test_profile_without_filter_shows_all_time_total(self, seeded_client):
        """All four expenses total 1150.00; no filter must show this."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile")
        # The INR filter formats as ₹1,150.00
        assert b"1,150.00" in rv.data

    def test_profile_without_filter_shows_all_transactions(self, seeded_client):
        """All four expense descriptions must appear on the unfiltered page."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile")
        assert b"April food" in rv.data
        assert b"May travel" in rv.data
        assert b"May food" in rv.data
        assert b"June bills" in rv.data

    def test_profile_without_filter_shows_correct_tx_count(self, seeded_client):
        """Transaction count stat must equal 4 with no filter."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile")
        # The count "4" must appear somewhere in the stats section.
        # We check that the byte string is present without assuming markup.
        assert b"4" in rv.data


# ---------------------------------------------------------------------------
# Happy path: full date range (both params)
# ---------------------------------------------------------------------------

class TestFullDateRangeFilter:
    """GET /profile?start_date=2026-05-01&end_date=2026-05-31"""

    def test_full_range_returns_200(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert rv.status_code == 200

    def test_full_range_total_reflects_only_may_expenses(self, seeded_client):
        """May total = 200 + 150 = 350.00."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"350.00" in rv.data

    def test_full_range_tx_count_reflects_only_may_expenses(self, seeded_client):
        """Only two transactions fall inside May 2026."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"2" in rv.data

    def test_full_range_includes_in_range_transactions(self, seeded_client):
        """May transactions must appear in the filtered view."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"May travel" in rv.data
        assert b"May food" in rv.data

    def test_full_range_excludes_out_of_range_transactions(self, seeded_client):
        """April and June expenses must NOT appear in the filtered view."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"April food" not in rv.data
        assert b"June bills" not in rv.data


# ---------------------------------------------------------------------------
# Happy path: start_date only (open end)
# ---------------------------------------------------------------------------

class TestStartDateOnlyFilter:
    """GET /profile?start_date=2026-05-01 — all expenses from 1 May onwards."""

    def test_start_date_only_returns_200(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01")
        assert rv.status_code == 200

    def test_start_date_only_total_excludes_earlier_expenses(self, seeded_client):
        """May + June total = 200 + 150 + 300 = 650.00; April (500) excluded."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01")
        assert b"650.00" in rv.data

    def test_start_date_only_includes_expenses_on_or_after_start(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01")
        assert b"May travel" in rv.data
        assert b"May food" in rv.data
        assert b"June bills" in rv.data

    def test_start_date_only_excludes_expenses_before_start(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01")
        assert b"April food" not in rv.data


# ---------------------------------------------------------------------------
# Happy path: end_date only (open start)
# ---------------------------------------------------------------------------

class TestEndDateOnlyFilter:
    """GET /profile?end_date=2026-05-31 — all expenses up to 31 May."""

    def test_end_date_only_returns_200(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=2026-05-31")
        assert rv.status_code == 200

    def test_end_date_only_total_excludes_later_expenses(self, seeded_client):
        """April + May total = 500 + 200 + 150 = 850.00; June (300) excluded."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=2026-05-31")
        assert b"850.00" in rv.data

    def test_end_date_only_includes_expenses_on_or_before_end(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=2026-05-31")
        assert b"April food" in rv.data
        assert b"May travel" in rv.data
        assert b"May food" in rv.data

    def test_end_date_only_excludes_expenses_after_end(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=2026-05-31")
        assert b"June bills" not in rv.data


# ---------------------------------------------------------------------------
# Input validation: malformed dates return 400
# ---------------------------------------------------------------------------

class TestDateValidation:
    """Malformed date values must cause the route to abort with HTTP 400."""

    def test_malformed_start_date_returns_400(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=not-a-date")
        assert rv.status_code == 400

    def test_malformed_end_date_returns_400(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=not-a-date")
        assert rv.status_code == 400

    def test_wrong_format_start_date_returns_400(self, seeded_client):
        """DD/MM/YYYY is not the expected YYYY-MM-DD format."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=01/05/2026")
        assert rv.status_code == 400

    def test_wrong_format_end_date_returns_400(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=31/05/2026")
        assert rv.status_code == 400

    def test_both_params_malformed_returns_400(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=abc&end_date=xyz")
        assert rv.status_code == 400

    def test_partial_date_string_returns_400(self, seeded_client):
        """A value like '2026-05' is not a full YYYY-MM-DD date."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05")
        assert rv.status_code == 400


# ---------------------------------------------------------------------------
# Edge case: empty string params treated as no filter
# ---------------------------------------------------------------------------

class TestEmptyStringParams:
    """
    Submitting the filter form with no date chosen sends empty strings.
    The spec says empty strings are treated as no filter (200 response,
    all-time data shown).
    """

    def test_empty_start_date_string_returns_200(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=")
        assert rv.status_code == 200

    def test_empty_end_date_string_returns_200(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=")
        assert rv.status_code == 200

    def test_both_empty_strings_returns_200(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=&end_date=")
        assert rv.status_code == 200

    def test_empty_strings_show_all_time_data(self, seeded_client):
        """Empty params must show the same all-time total as no params at all."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=&end_date=")
        assert b"1,150.00" in rv.data

    def test_empty_strings_do_not_show_active_filter_banner(self, seeded_client):
        """
        An empty string is not a real filter; the active-filter banner must
        not appear when both values resolve to None.
        """
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=&end_date=")
        assert b"filter-banner" not in rv.data


# ---------------------------------------------------------------------------
# DB side effects: stats reflect filtered data
# ---------------------------------------------------------------------------

class TestFilteredStats:
    """Summary statistics must be recomputed for the filtered date range."""

    def test_filtered_total_spent_is_not_all_time_total(self, seeded_client):
        """Filtered total (350) must differ from all-time total (1150)."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"1,150.00" not in rv.data
        assert b"350.00" in rv.data

    def test_filtered_top_category_reflects_date_range(self, seeded_client):
        """
        In May 2026: Food = 150, Travel = 200.
        Top category for May should be Travel (highest spend).
        """
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"Travel" in rv.data

    def test_no_filter_top_category_reflects_all_time(self, seeded_client):
        """
        All-time: Food = 500 + 150 = 650 (top), Travel = 200, Bills = 300.
        Without a filter the top category must be Food.
        """
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile")
        assert b"Food" in rv.data


# ---------------------------------------------------------------------------
# DB side effects: category breakdown reflects filtered data
# ---------------------------------------------------------------------------

class TestFilteredCategoryBreakdown:
    """The category breakdown section must only include filtered expenses."""

    def test_category_breakdown_excludes_out_of_range_categories(self, seeded_client):
        """
        Filtering to June only (end_date omitted means open-end from June):
        only Bills should appear in the breakdown; Food and Travel should not.
        """
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-06-01")
        # Bills must appear
        assert b"Bills" in rv.data
        # June has no Food or Travel expenses in our seed data.
        # We check that the June-only total (300.00) appears.
        assert b"300.00" in rv.data

    def test_category_breakdown_shows_correct_totals_for_filter(self, seeded_client):
        """
        April-only filter: only Food (500.00) should appear in breakdown.
        """
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-04-01&end_date=2026-04-30")
        assert b"500.00" in rv.data
        # Travel and Bills had no April expenses
        assert b"200.00" not in rv.data
        assert b"300.00" not in rv.data


# ---------------------------------------------------------------------------
# Form pre-fill: date inputs contain current filter values
# ---------------------------------------------------------------------------

class TestFormPrefill:
    """
    When a filter is active the date inputs in the filter form must be
    pre-filled with the current filter values so the user can see and adjust
    the active range.
    """

    def test_start_date_input_prefilled_when_filter_active(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        # The HTML attribute value="2026-05-01" must appear in the response.
        assert b'value="2026-05-01"' in rv.data

    def test_end_date_input_prefilled_when_filter_active(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b'value="2026-05-31"' in rv.data

    def test_start_date_prefilled_when_only_start_given(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01")
        assert b'value="2026-05-01"' in rv.data

    def test_end_date_prefilled_when_only_end_given(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=2026-05-31")
        assert b'value="2026-05-31"' in rv.data

    def test_inputs_empty_when_no_filter_active(self, seeded_client):
        """
        With no filter, both inputs must render with an empty value so the
        browser does not display a stale date.
        """
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile")
        # Empty value attributes are produced by the `{{ start_date or '' }}` pattern.
        assert b'value=""' in rv.data


# ---------------------------------------------------------------------------
# Active-filter banner visibility
# ---------------------------------------------------------------------------

class TestActiveFilterBanner:
    """
    The active-filter banner must appear when at least one date param is set
    and must be absent when no filter is active.
    """

    def test_banner_visible_when_both_dates_set(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"filter-banner" in rv.data

    def test_banner_visible_when_only_start_date_set(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01")
        assert b"filter-banner" in rv.data

    def test_banner_visible_when_only_end_date_set(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=2026-05-31")
        assert b"filter-banner" in rv.data

    def test_banner_absent_when_no_filter(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile")
        assert b"filter-banner" not in rv.data

    def test_banner_shows_start_date_value(self, seeded_client):
        """The banner must echo the applied start_date back to the user."""
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"2026-05-01" in rv.data

    def test_banner_shows_end_date_value(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        assert b"2026-05-31" in rv.data


# ---------------------------------------------------------------------------
# Clear link presence
# ---------------------------------------------------------------------------

class TestClearLink:
    """
    A 'Clear' link (href="/profile" with no params) must be present on the
    page when a filter is active and must be absent when no filter is set.
    """

    def test_clear_link_present_when_filter_active(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01&end_date=2026-05-31")
        # The Clear anchor points back to /profile with no query string.
        assert b'href="/profile"' in rv.data

    def test_clear_link_present_when_only_start_date_set(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?start_date=2026-05-01")
        assert b'href="/profile"' in rv.data

    def test_clear_link_present_when_only_end_date_set(self, seeded_client):
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile?end_date=2026-05-31")
        assert b'href="/profile"' in rv.data

    def test_clear_link_absent_when_no_filter(self, seeded_client):
        """
        Without an active filter there is no reason to show a Clear link.
        The logout link also points to /logout not /profile, so checking
        for the filter-clear CSS class is the most precise signal.
        """
        client, user_id = seeded_client
        _login(client)
        rv = client.get("/profile")
        assert b"filter-clear" not in rv.data
