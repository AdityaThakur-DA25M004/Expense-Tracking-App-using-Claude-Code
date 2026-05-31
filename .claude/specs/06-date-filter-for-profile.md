# Spec: Date Filter for Profile

## Overview
This feature adds a date range filter to the profile page, allowing users to narrow the transactions list and summary stats to a specific period. Users can select a start date, an end date, or both — the profile page then re-renders showing only expenses within that range. This is the first interactive filtering capability in Spendly and makes the profile page genuinely useful for reviewing spending over a pay period, month, or custom window.

## Depends on
- Step 01 — Database setup (expenses table with `date` column)
- Step 04 — Profile page template
- Step 05 — Backend routes for profile page (`get_summary_stats`, `get_recent_transactions`, `get_category_breakdown` in `database/queries.py`)

## Routes
- `GET /profile` — Modified to accept optional query parameters `start_date` and `end_date` (YYYY-MM-DD). When either is present, all data helpers are called with the date range. — logged-in only

No new routes.

## Database changes
No database changes. The `expenses.date` column already stores ISO 8601 dates (YYYY-MM-DD), which SQLite's `BETWEEN` operator supports natively.

## Templates
- **Modify:** `templates/profile.html`
  - Add a date filter form above the Recent Transactions section
  - Two date inputs (`start_date`, `end_date`) and a "Filter" submit button
  - A "Clear" link that navigates to `/profile` with no query params
  - Show an active-filter banner when a filter is applied (e.g. "Showing: 01 May 2026 – 31 May 2026")

## Files to change
- `app.py` — modify the `GET /profile` route to read `start_date` and `end_date` from `request.args`, validate them, and pass them to query helpers
- `database/queries.py` — update `get_summary_stats`, `get_recent_transactions`, and `get_category_breakdown` to accept optional `start_date` / `end_date` parameters and apply `WHERE e.date BETWEEN ? AND ?` when provided
- `templates/profile.html` — add date filter UI
- `static/css/style.css` — add styles for the filter form and active-filter banner

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw SQLite only via `get_db()`
- Parameterised queries only — never interpolate dates into SQL strings
- Passwords hashed with werkzeug (existing behaviour, unchanged)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate date inputs in the route with `datetime.strptime(val, "%Y-%m-%d")` — if either value is malformed, call `abort(400)`
- If only `start_date` is provided, filter `e.date >= start_date`; if only `end_date`, filter `e.date <= end_date`; if both, use `BETWEEN`
- Pass `start_date` and `end_date` back to the template so the form fields are pre-filled and the active-filter banner can be displayed
- Do not change any route other than `GET /profile`
- Do not remove or change the existing default behaviour (no params → show all transactions)

## Definition of done
- [ ] Visiting `/profile` with no query params renders the page exactly as before (no regression)
- [ ] Visiting `/profile?start_date=2026-05-01&end_date=2026-05-31` shows only expenses dated within May 2026
- [ ] The date filter form on the profile page is pre-filled with the current filter values when a filter is active
- [ ] An active-filter banner is visible when at least one date param is present
- [ ] The "Clear" link navigates to `/profile` and removes the filter
- [ ] Passing a malformed date (e.g. `?start_date=not-a-date`) returns a 400 response
- [ ] Summary stats (total spent, transaction count, top category) reflect the filtered date range
- [ ] Category breakdown reflects the filtered date range
- [ ] Providing only `start_date` or only `end_date` works correctly (open-ended range)
