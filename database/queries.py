from datetime import datetime

import database.db as db


def _build_date_clause(start_date, end_date):
    if start_date and end_date:
        return "e.date BETWEEN ? AND ?", [start_date, end_date]
    if start_date:
        return "e.date >= ?", [start_date]
    if end_date:
        return "e.date <= ?", [end_date]
    return "", []


def _build_where(user_id, start_date, end_date):
    date_clause, date_params = _build_date_clause(start_date, end_date)
    where = "e.user_id = ?"
    params = [user_id]
    if date_clause:
        where += " AND " + date_clause
        params.extend(date_params)
    return where, params


def get_user_by_id(user_id):
    conn = db.get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    try:
        member_since = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")
    except ValueError:
        member_since = row["created_at"][:7]

    return {"name": row["name"], "email": row["email"], "member_since": member_since}


def get_summary_stats(user_id, start_date=None, end_date=None):
    where, params = _build_where(user_id, start_date, end_date)

    conn = db.get_db()
    try:
        totals = conn.execute(
            "SELECT COALESCE(SUM(e.amount), 0.0) AS total_spent, COUNT(e.id) AS tx_count"
            " FROM expenses e WHERE " + where,
            params,
        ).fetchone()
        top = conn.execute(
            "SELECT c.name FROM expenses e"
            " JOIN categories c ON c.id = e.category_id"
            " WHERE " + where + " GROUP BY c.id ORDER BY SUM(e.amount) DESC LIMIT 1",
            params,
        ).fetchone()
    finally:
        conn.close()

    return {
        "total_spent": totals["total_spent"],
        "tx_count": totals["tx_count"],
        "top_category": top["name"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    where, params = _build_where(user_id, start_date, end_date)
    params.append(limit)

    conn = db.get_db()
    try:
        rows = conn.execute(
            "SELECT e.date, e.description, c.name AS category, e.amount"
            " FROM expenses e JOIN categories c ON c.id = e.category_id"
            " WHERE " + where + " ORDER BY e.date DESC, e.id DESC LIMIT ?",
            params,
        ).fetchall()
    finally:
        conn.close()

    result = []
    for row in rows:
        try:
            display_date = datetime.strptime(row["date"], "%Y-%m-%d").strftime("%d %b %Y")
        except ValueError:
            display_date = row["date"]
        result.append({
            "date": display_date,
            "description": row["description"],
            "category": row["category"],
            "amount": row["amount"],
        })
    return result


def get_category_breakdown(user_id, start_date=None, end_date=None):
    where, params = _build_where(user_id, start_date, end_date)

    conn = db.get_db()
    try:
        rows = conn.execute(
            "SELECT c.name, SUM(e.amount) AS total"
            " FROM expenses e JOIN categories c ON c.id = e.category_id"
            " WHERE " + where + " GROUP BY c.id ORDER BY total DESC",
            params,
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    grand_total = sum(r["total"] for r in rows)
    int_pcts = [int(r["total"] / grand_total * 100) for r in rows]
    int_pcts[0] += 100 - sum(int_pcts)

    return [
        {"name": r["name"], "total": float(r["total"]), "pct": pct}
        for r, pct in zip(rows, int_pcts)
    ]
