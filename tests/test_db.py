import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app
import database.db as db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = ':memory:'
    with app.test_client() as client:
        with app.app_context():
            # Override database for testing if needed, or test db functions directly
            pass
        yield client

def test_database_initialization_and_seeding(tmp_path):
    # Test db helpers with a temporary database path
    db_file = tmp_path / "test_spendly.db"
    db.DATABASE = str(db_file)

    with app.app_context():
        db.init_db()
        db.seed_db()

        conn = db.get_db()

        # Check tables exist
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert 'users' in tables
        assert 'expenses' in tables

        # Check demo user
        user = conn.execute("SELECT * FROM users WHERE email = 'demo@spendly.com'").fetchone()
        assert user is not None
        assert user['name'] == 'Demo User'

        # Check expenses
        expenses = conn.execute("SELECT * FROM expenses WHERE user_id = ?", (user['id'],)).fetchall()
        assert len(expenses) == 8

        categories = {e['category'] for e in expenses}
        expected_categories = {'Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other'}
        assert expected_categories.issubset(categories)

        # Test idempotency of seed_db
        db.seed_db()
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 8
