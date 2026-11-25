# Spec: Login and Logout

## Overview
Implement user login functionality allowing registered users to authenticate with their email and password. This step adds the POST handler for `/login` to verify credentials against the database, create a session on success, and redirect to the profile page. The `/logout` route is already implemented as a stub from Step 2 and will be fully functional after this step. This completes the core authentication flow started in Step 2 (Registration).

## Depends on
- Step 01: Database Setup (users table, `get_db()`, `init_db()`, `seed_db()`)
- Step 02: Registration (user creation, password hashing, session handling)

## Routes
- `GET /login` — renders login form (already exists)
- `POST /login` — handles form submission, verifies credentials, starts session — public access
- `GET /logout` — clears session and redirects to landing — logged-in access (already implemented as stub, now functional)

## Database changes
No new tables or columns. Uses existing `users` table from Step 01.

## Templates
- **Modify:** `templates/login.html` — ensure error message display works with POST handler
- **No new templates needed** — existing `login.html` has the form

## Files to change
- `app.py` — add POST `/login` handler with credential verification and session creation
- `database/db.py` — no new helpers needed (uses existing `get_user_by_email()`)

## Files to create
- None

## New dependencies
No new dependencies. Uses:
- `werkzeug.security.check_password_hash` (already in requirements)
- `werkzeug.security.generate_password_hash` (already in requirements, used in registration)
- Flask `session` (built-in)

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — use `?` placeholders
- Passwords verified with `werkzeug.security.check_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for all internal links
- No DB logic in route functions — use `database/db.py` helpers
- Store `user_id` and `user_name` in Flask session on successful login
- Clear session on logout
- On failed login, re-render template with error message (don't redirect)

## Definition of done
- [ ] `POST /login` accepts email and password
- [ ] Validates: both fields present
- [ ] Looks up user by email using `get_user_by_email()`
- [ ] Verifies password with `check_password_hash`
- [ ] On success: creates Flask session with `user_id` and `user_name`
- [ ] On success: redirects to `/profile` (stub)
- [ ] On failure: re-renders `login.html` with error message
- [ ] `GET /logout` clears session and redirects to `/`
- [ ] Flash/error messages displayed in template
- [ ] No SQL injection vulnerabilities (parameterized queries)
- [ ] App starts without errors
- [ ] Demo user (demo@spendly.com / demo123) can log in successfully