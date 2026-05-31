# Spec: Login and Logout

## Overview
Step 3 activates the login form and wires up session management. The `GET /login` route and `login.html` template already exist; this step adds the `POST /login` handler that verifies the submitted credentials against the database, stores the authenticated user's ID in Flask's signed session cookie, and redirects to `/profile` on success. `GET /logout` is upgraded from its stub to a real handler that clears the session and redirects to `/`. The seed user's plaintext password is also replaced with a proper Werkzeug hash so the demo account works end-to-end. After this step, Spendly has a functioning auth layer that later steps can build on.

## Depends on
- Step 1 — Database setup (`users` table, `get_db()`, `init_db()`)
- Step 2 — Registration (`get_user_by_email()` helper, `app.secret_key` set)

## Routes
- `POST /login` — accepts email/password form fields, verifies credentials, stores `user_id` in session, redirects to `/profile` on success, re-renders `login.html` with error on failure — public
- `GET /logout` — clears the Flask session, redirects to `/` — public (no auth guard needed)

## Database changes
No new tables or columns. `seed_db()` in `database/db.py` must be updated to store the demo user's password as a Werkzeug hash instead of the current plaintext string.

## Templates
- **Modify:** `templates/login.html` — ensure `<form>` has `method="POST"` and `action="{{ url_for('login') }}"`, and renders `{{ error }}` when present
- **Modify:** `templates/base.html` — add a logout link (`url_for('logout')`) visible only when a user is logged in (check `session.get('user_id')`)

## Files to change
- `app.py` — convert `/login` to handle both GET and POST; implement `POST /login` (validate fields, call `get_user_by_email`, verify hash, set `session['user_id']`, redirect); upgrade `/logout` stub to clear session and redirect; import `session` from Flask, `check_password_hash` from `werkzeug.security`
- `database/db.py` — update `seed_db()` to hash the demo user's password with `generate_password_hash` before inserting
- `templates/login.html` — add `method="POST"` and `url_for('login')` action; ensure `{{ error }}` variable is rendered
- `templates/base.html` — add conditional logout link using `session.get('user_id')`

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security` (`check_password_hash`) is already available via `werkzeug==3.1.6` in `requirements.txt`. Flask's `session` is built-in.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — never f-strings in SQL
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plain-text
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB helpers go in `database/db.py` — no SQL inside route functions
- User-visible validation errors (wrong password, blank fields, unknown email) re-render `login.html` with an `error=` variable — do not use `abort()` for those; use the same generic message for wrong email and wrong password to avoid user enumeration
- On successful login redirect to `url_for('profile')` — do not render a template
- On logout redirect to `url_for('landing')` — do not render a template
- `session['user_id']` must store an integer (the `users.id` value), not the email or name
- Do not add a `login_required` decorator in this step — that belongs to a later step

## Definition of done
- [ ] Submitting the login form with the correct email and password stores `user_id` in the session and redirects to `/profile`
- [ ] Submitting with a wrong password re-renders `login.html` with a visible error message
- [ ] Submitting with an unknown email re-renders `login.html` with a visible error message (same message as wrong password — no enumeration)
- [ ] Submitting with any blank field re-renders `login.html` with a visible error message
- [ ] `GET /logout` clears the session and redirects to `/`
- [ ] After logout, the session no longer contains `user_id`
- [ ] The demo seed user (`demo@spendly.com` / `demo1234`) can log in successfully (password stored as a hash after `seed_db()` runs)
- [ ] The logout link is visible in `base.html` only when a user is logged in
- [ ] `GET /login` still works and renders the empty form (no regression)
- [ ] No SQL is written inside route functions — all DB calls go through `database/db.py`
