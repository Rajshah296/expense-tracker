# Implementation Plan: Registration (Step 02)

## Context
This is Step 2 of the Spendly expense tracker roadmap. Step 1 (Database Setup) is complete — the `users` and `expenses` tables exist with a demo user seeded. This step implements user registration: handling the POST request from the existing `/register` form, validating input, hashing passwords, creating users in the database, and establishing a Flask session. It also implements the `/logout` route (currently a stub in `app.py`).

## Current State
- `app.py`: Has GET `/register`, GET `/login`, GET `/logout` (stub), GET `/profile` (stub)
- `database/db.py`: Has `get_db()`, `init_db()`, `seed_db()` — needs `create_user()` and `get_user_by_email()`
- `templates/register.html`: Form exists with POST to `/register`, displays `error` variable
- `templates/base.html`: No flash message display, no user-aware navigation
- `requirements.txt`: Flask 3.1.3, Werkzeug 3.1.6 available

## Implementation Plan

### 1. Update `database/db.py`
Add two new helper functions:

**`get_user_by_email(email: str) -> sqlite3.Row | None`**
- Parameterized query: `SELECT * FROM users WHERE email = ?`
- Returns user row or None

**`create_user(name: str, email: str, password_hash: str) -> int`**
- Parameterized query: `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)`
- Returns `lastrowid` (new user's ID)
- Let UNIQUE constraint on email raise `sqlite3.IntegrityError` for duplicate emails

### 2. Update `app.py`
**Imports to add:**
```python
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_user_by_email, create_user
```

**Secret key:** Add `app.secret_key = 'dev-secret-change-in-production'` (or load from env)

**Route: `POST /register`**
```python
@app.route("/register", methods=["POST"])
def register_post():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    
    # Validation
    if not name or not email or not password:
        return render_template("register.html", error="All fields are required")
    if "@" not in email or "." not in email:
        return render_template("register.html", error="Invalid email format")
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters")
    
    # Check duplicate
    if get_user_by_email(email):
        return render_template("register.html", error="Email already registered")
    
    # Create user
    password_hash = generate_password_hash(password)
    user_id = create_user(name, email, password_hash)
    
    # Start session
    session["user_id"] = user_id
    session["user_name"] = name
    
    return redirect(url_for("profile"))
```

**Route: `GET /logout`** (replace stub)
```python
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))
```

**Route: `GET /register`** (keep existing, but ensure it passes `error=None` by default)

### 3. Update `templates/register.html`
The template already has `{% if error %}` block. No changes strictly needed, but optionally add a success message block (not required per spec).

### 4. Update `templates/base.html` (optional but recommended)
Add flash message display in main content area:
```html
<main class="main-content">
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <div class="flash-messages">
                {% for message in messages %}
                    <div class="flash-message">{{ message }}</div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
</main>
```
And update nav to show user name when logged in (requires session check in template or context processor).

## Files to Modify
1. `database/db.py` — add `get_user_by_email()`, `create_user()`
2. `app.py` — add imports, secret_key, POST `/register`, replace `/logout` stub
3. `templates/base.html` — add flash message display (optional but good practice)

## Verification Steps
1. Start app: `python app.py` (port 5001)
2. Visit `http://localhost:5001/register`
3. Submit valid form → should redirect to `/profile` (stub page)
4. Verify session cookie set in browser dev tools
5. Visit `http://localhost:5001/logout` → should redirect to `/`
6. Verify session cleared
7. Test validation: empty fields, short password, invalid email, duplicate email
8. Run tests: `pytest tests/ -v`

## Test Cases to Add (in `tests/test_db.py` or new `tests/test_auth.py`)
- `test_register_valid_input` — creates user, sets session
- `test_register_duplicate_email` — returns error
- `test_register_validation` — empty fields, short password, bad email
- `test_logout_clears_session`

## Dependencies
No new packages. Uses existing: `flask`, `werkzeug.security`, `sqlite3`.