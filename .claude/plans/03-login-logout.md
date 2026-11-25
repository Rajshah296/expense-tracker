# Implementation Plan: Login and Logout (Step 03)

## Context
This step implements the POST `/login` handler to complete the core authentication flow. The GET `/login` route and template already exist, and the `/logout` route is already implemented as a stub. This builds on Step 02 (Registration) which established the session pattern, password hashing, and database helpers.

## Files to Modify

### 1. `app.py`
**Changes needed:**
- Import `check_password_hash` from `werkzeug.security` (line 2)
- Modify the `/login` route (lines 57-59) to handle both GET and POST methods
- Add POST handler logic following the same pattern as `/register`:
  - Extract email and password from form
  - Validate both fields are present
  - Look up user by email using `get_user_by_email()`
  - Verify password with `check_password_hash()`
  - On success: set `session["user_id"]` and `session["user_name"]`, flash success, redirect to `/profile`
  - On failure: re-render `login.html` with error message

### 2. `templates/login.html` (no changes needed)
The template already has:
- Form with `method="POST"` and `action="/login"`
- Error display block: `{% if error %}<div class="auth-error">{{ error }}</div>{% endif %}`
- Email and password inputs with proper names
- Extends `base.html` and uses `url_for()`

## Implementation Details

### Route Pattern (matching `/register`)
```python
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validation
        if not email or not password:
            return render_template("login.html", error="Both fields are required")

        # Look up user
        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password")

        # Start session
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        flash("Signed in successfully!")
        return redirect(url_for("profile"))

    return render_template("login.html")
```

### Import Addition
```python
from werkzeug.security import generate_password_hash, check_password_hash
```

## Verification Steps

1. **Start the app:** `python app.py` (runs on port 5001)
2. **Test GET /login:** Navigate to `http://localhost:5001/login` - should render login form
3. **Test failed login:** Submit empty form - should show "Both fields are required"
4. **Test failed login:** Submit invalid credentials - should show "Invalid email or password"
5. **Test successful login:** Use demo user `demo@spendly.com` / `demo123` - should redirect to `/profile` (stub page)
6. **Test logout:** Navigate to `/logout` - should clear session, flash message, redirect to landing
7. **Verify session persistence:** After login, visit `/profile` - should show stub (session maintained)
8. **Run tests:** `pytest` (if any exist)

## Dependencies
- No new packages needed
- Uses existing: `werkzeug.security.check_password_hash`, `werkzeug.security.generate_password_hash`, Flask `session`

## Constraints Followed
- No SQLAlchemy/ORMs
- Parameterized queries only (via existing `get_user_by_email`)
- Passwords verified with `check_password_hash`
- CSS variables only (no template changes needed)
- All templates extend `base.html`
- `url_for()` for internal links
- No DB logic in routes (uses `database/db.py` helpers)
- Session stores `user_id` and `user_name`
- On failed login, re-renders template with error (no redirect)