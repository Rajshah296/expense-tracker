import sqlite3
from flask import g
from werkzeug.security import generate_password_hash

DATABASE = 'spendly.db'


def get_db():
    """Get the database connection for the current request context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
    return db


def close_db(exception=None):
    """Close the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize the database tables (users and expenses)."""
    db = get_db()

    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    db.commit()


def seed_db():
    """Seed the database with a demo user and 8 sample expenses if not already seeded."""
    db = get_db()

    # Check if users table already has records
    cursor = db.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]

    if count > 0:
        return  # Already seeded

    # Insert demo user
    password_hash = generate_password_hash('demo123')
    cursor = db.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('Demo User', 'demo@spendly.com', password_hash)
    )
    user_id = cursor.lastrowid

    # Insert 8 sample expenses covering all specified categories
    sample_expenses = [
        (user_id, 14.50, 'Food', '2026-11-01', 'Morning coffee and pastry'),
        (user_id, 45.00, 'Transport', '2026-11-03', 'Monthly subway pass'),
        (user_id, 120.00, 'Bills', '2026-11-05', 'Electric utility bill'),
        (user_id, 65.00, 'Health', '2026-11-08', 'Pharmacy prescription refill'),
        (user_id, 32.80, 'Food', '2026-11-10', 'Grocery shopping at local market'),
        (user_id, 55.00, 'Entertainment', '2026-11-12', 'Movie tickets and snacks'),
        (user_id, 89.99, 'Shopping', '2026-11-15', 'New running shoes'),
        (user_id, 18.00, 'Other', '2026-11-18', 'Stationery and pens')
    ]

    db.executemany(
        'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
        sample_expenses
    )

    db.commit()
