import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import init_db, seed_db, get_user_by_email, get_user_by_id, create_user

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.")
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")
    if get_user_by_email(email):
        return render_template("register.html", error="An account with that email already exists.")

    create_user(name, email, generate_password_hash(password))
    return redirect(url_for('login'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    error = "Invalid email or password."

    if not email or not password:
        return render_template("login.html", error=error)

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password"], password):
        return render_template("login.html", error=error)

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    user = get_user_by_id(session["user_id"])
    if user is None:
        session.clear()
        return redirect(url_for("login"))

    stats = {
        "total_spent": "₹3,240.00",
        "tx_count": 12,
        "top_category": "Food",
    }
    transactions = [
        {"date": "28 May 2025", "description": "Lunch at canteen",  "category": "Food",     "amount": "₹450.00"},
        {"date": "27 May 2025", "description": "Metro card top-up", "category": "Travel",   "amount": "₹120.00"},
        {"date": "26 May 2025", "description": "Coffee and snacks", "category": "Food",     "amount": "₹85.50"},
        {"date": "25 May 2025", "description": "Electricity bill",  "category": "Bills",    "amount": "₹980.00"},
        {"date": "24 May 2025", "description": "Weekend groceries", "category": "Shopping", "amount": "₹640.00"},
    ]
    categories = [
        {"name": "Food",        "total": "₹1,420.00", "pct": 44},
        {"name": "Bills",       "total": "₹980.00",   "pct": 30},
        {"name": "Shopping",    "total": "₹640.00",   "pct": 20},
        {"name": "Travel",      "total": "₹120.00",   "pct": 4},
        {"name": "Health",      "total": "₹80.00",    "pct": 2},
    ]
    return render_template("profile.html", user=user,
                           stats=stats, transactions=transactions,
                           categories=categories)


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    init_db()
    seed_db()
    app.run(debug=True, port=5001)
