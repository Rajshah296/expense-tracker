## Spec: Registration

### Overview
Implement user registration functionality allowing new users to create an account with name, email, and password. This is the first authentication feature and enables users to access the expense tracking features. The registration form already exists in `templates/register.html` — this step adds the POST handler, password hashing, database insertion, and session creation.

### Depends on
- Step 01: Database Setup (users table, `get_db()`, `init_db()`, `seed_db()`)

### Routes
- `GET /register` — renders registration form (already exists)
- `POST /register` — handles form submission, creates user, starts session — public access
- `GET /logout` — clears session and redirects to landing — logged-in access (moved from stub)

### Database changes
No new tables or columns. Uses existing `users` table from Step 01.

### Templates
- **Modify:** `templates/register.html` — add `{% if success %}` block for success message (optional)
- **No new templates needed** — existing `register.html` has the form

### Files to change
- `app.py` — add POST `/register` handler, implement `/logout`, add session handling
- `database/db.py` — add `create_user()` and `get_user_by_email()` helpers

### Files to create
- None

### New dependencies
No new dependencies. Uses:
- `werkzeug.security.generate_password_hash` (already in requirements)
- `werkzeug.security.check_password_hash` (already in requirements)
- Flask `session` (built-in)

### Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — use `?` placeholders
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for all internal links
- No DB logic in route functions — use `database/db.py` helpers
- Store `user_id` in Flask session on successful registration/login
- Clear session on logout

### Definition of done
- [ ] `POST /register` accepts name, email, password
- [ ] Validates: all fields present, email format, password ≥ 8 chars
- [ ] Rejects duplicate email with user-friendly error
- [ ] Hashes password with `generate_password_hash`
- [ ] Inserts user into `users` table
- [ ] Creates Flask session with `user_id`
- [ ] Redirects to `/profile` (stub) on success
- [ ] `GET /logout` clears session and redirects to `/`
- [ ] Flash/error messages displayed in template
- [ ] No SQL injection vulnerabilities (parameterized queries)
- [ ] App starts without errors