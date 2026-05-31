# Spec: Registration

## Overview
Step 2 wires up the registration form so new users can create an account. The `GET /register` route and `register.html` template already exist from the landing-page work; this step adds the `POST /register` handler that validates the submitted data, hashes the password with Werkzeug, inserts the new user into the database, and redirects to the login page on success. Duplicate-email and missing-field errors are surfaced back to the form via a template variable.

## Depends on
- Step 1 — Database setup (users table in `database/db.py`, `init_db()` functional)

## Routes
- `POST /register` — accepts name/email/password form fields, validates, creates user, redirects to `/login` — public

## Database changes
No new tables or columns. The `users` table (id, name, email, password, created_at) already exists from Step 1. No schema changes needed.

## Templates
- **Modify:** `templates/register.html` — form action already points to `POST /register`; the template already renders `{{ error }}` — no structural changes required, but use `url_for('register')` in the action attribute instead of the hardcoded `/register` string.

## Files to change
- `app.py` — add `POST /register` route; add `app.secret_key` (required for `flash()`/session even if not used yet; guards against future foot-guns); import `redirect`, `url_for`, `request` from Flask
- `database/db.py` — add `create_user(name, email, password_hash)` and `get_user_by_email(email)` helpers
- `templates/register.html` — replace hardcoded action URL with `url_for('register')`

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` (generate_password_hash) is already in `requirements.txt` via `werkzeug==3.1.6`.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — never f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` — never stored plain-text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB helpers go in `database/db.py` — no SQL inside route functions
- The route must call `abort(400)` only for truly malformed requests; user-visible validation errors (duplicate email, blank fields) re-render `register.html` with an `error=` variable — do not use `abort()` for those
- `app.secret_key` must be set before any session/flash usage; use `os.urandom(24)` for a dev default guarded by an env var so production can override it
- On success redirect to `url_for('login')` — do not render a template

## Definition of done
- [ ] Submitting the form with valid name/email/password inserts a row into `users` and redirects to `/login`
- [ ] The stored password is a Werkzeug hash, not plain-text
- [ ] Submitting with a duplicate email re-renders the form with a visible error message
- [ ] Submitting with any blank field re-renders the form with a visible error message
- [ ] Password shorter than 8 characters re-renders the form with a visible error message
- [ ] `GET /register` still works and renders the empty form (no regression)
- [ ] No SQL is written inside the route function — all DB calls go through `database/db.py`
