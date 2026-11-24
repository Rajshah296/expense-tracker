# Context

This plan outlines the implementation for **Step 1: Database Setup** in Spendly. The goal is to establish the SQLite database connection, table schemas (`users` and `expenses`), and seeding logic in `database/db.py`, and hook database initialization and seeding into the Flask application startup in `app.py`.

---

## 1. Requirements Summary (`.claude/specs/01-database-setup.md`)

- **Database Connection (`get_db()`):**
  - Connects to `spendly.db` in the project root.
  - Sets `row_factory = sqlite3.Row` for dictionary-like column access.
  - Enforces manual foreign key constraints (`PRAGMA foreign_keys = ON`).
  - Uses Flask's application context (`g`) for request-scoped connection handling.

- **Database Initialization (`init_db()`):**
  - Creates `users` table: `id`, `name`, `email` (UNIQUE), `password_hash`, `created_at`.
  - Creates `expenses` table: `id`, `user_id` (FOREIGN KEY referencing `users.id`), `amount`, `category`, `date`, `description`, `created_at`.
  - Uses `CREATE TABLE IF NOT EXISTS` for safe, idempotent startup execution.

- **Database Seeding (`seed_db()`):**
  - Checks if `users` table is already populated; returns early if so.
  - Inserts one demo user (`Demo User`, `demo@spendly.com`, hashed password via Werkzeug).
  - Inserts 8 sample expenses linked to the demo user across all fixed categories (`Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`) with `YYYY-MM-DD` dates.

- **Application Integration (`app.py`):**
  - Imports `get_db`, `init_db`, `seed_db` from `database.db`.
  - Calls `init_db()` and `seed_db()` within `app.app_context()` on startup.
  - Registers teardown handler to close database connections.

---

## 2. Critical Files to Modify

- `/media/raj/D/expense-tracker/database/db.py`
- `/media/raj/D/expense-tracker/app.py`

---

## 3. Implementation Steps

1. **Implement `database/db.py`:**
   - Define `DATABASE = 'spendly.db'`.
   - Implement `get_db()`, `init_db()`, and `seed_db()`.
   - Implement `close_db(exception)` teardown helper.

2. **Update `app.py`:**
   - Import `get_db`, `init_db`, `seed_db` from `database.db`.
   - Add teardown hook: `app.teardown_appcontext(close_db)`.
   - Add startup initialization block:
     ```python
     with app.app_context():
         init_db()
         seed_db()
     ```

---

## 4. Verification Plan

1. **Interactive Check:**
   - Run python to invoke `init_db()` and `seed_db()` and verify `spendly.db` is created.
   - Verify `get_db()` returns rows with `sqlite3.Row` and foreign key enforcement enabled.
   - Verify calling `seed_db()` a second time does not duplicate records.
2. **Database Schema & Data Check:**
   - Inspect tables with `sqlite3 spendly.db ".schema"` and check contents.
3. **Automated Tests:**
   - Run `pytest` to ensure all tests pass successfully.
