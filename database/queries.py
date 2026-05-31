from datetime import datetime

import database.db as db


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


def get_summary_stats(user_id):
    conn = db.get_db()
    try:
        totals = conn.execute(
            "SELECT COALESCE(SUM(e.amount), 0.0) AS total_spent, COUNT(e.id) AS tx_count"
            " FROM expenses e WHERE e.user_id = ?",
            (user_id,),
        ).fetchone()
        top = conn.execute(
            "SELECT c.name FROM expenses e"
            " JOIN categories c ON c.id = e.category_id"
            " WHERE e.user_id = ? GROUP BY c.id ORDER BY SUM(e.amount) DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    return {
        "total_spent": totals["total_spent"],
        "tx_count": totals["tx_count"],
        "top_category": top["name"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10):
    conn = db.get_db()
    try:
        rows = conn.execute(
            "SELECT e.date, e.description, c.name AS category, e.amount"
            " FROM expenses e JOIN categories c ON c.id = e.category_id"
            " WHERE e.user_id = ? ORDER BY e.date DESC, e.id DESC LIMIT ?",
            (user_id, limit),
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


def get_category_breakdown(user_id):
    conn = db.get_db()
    try:
        rows = conn.execute(
            "SELECT c.name, SUM(e.amount) AS total"
            " FROM expenses e JOIN categories c ON c.id = e.category_id"
            " WHERE e.user_id = ? GROUP BY c.id ORDER BY total DESC",
            (user_id,),
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
