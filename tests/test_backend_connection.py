"""Tests for backend connection (Step 5): query helpers and /profile route."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app
import database.db as db
import database.queries as queries


@pytest.fixture
def app_context(tmp_path):
    """Create app context with temporary database."""
    db_file = tmp_path / "test_spendly.db"
    db.DATABASE = str(db_file)

    with app.app_context():
        db.init_db()
        db.seed_db()
        yield


def get_seed_user_id():
    """Get the demo user's ID from the seeded database."""
    conn = db.get_db()
    user = conn.execute("SELECT id FROM users WHERE email = 'demo@spendly.com'").fetchone()
    return user['id'] if user else None


# ============================================================
# Unit tests for query helpers
# ============================================================

def test_get_user_by_id_valid(app_context):
    user_id = get_seed_user_id()
    assert user_id is not None

    user = queries.get_user_by_id(user_id)
    assert user is not None
    assert user['name'] == 'Demo User'
    assert user['email'] == 'demo@spendly.com'
    assert user['member_since'] == 'November 2026'
    assert user['initials'] == 'D'


def test_get_user_by_id_invalid(app_context):
    user = queries.get_user_by_id(99999)
    assert user is None


def test_get_summary_stats_with_expenses(app_context):
    user_id = get_seed_user_id()
    assert user_id is not None

    stats = queries.get_summary_stats(user_id)
    assert abs(stats['total_spent'] - 440.29) < 0.01  # Sum of all 8 seed expenses (float precision)
    assert stats['transaction_count'] == 8
    assert stats['top_category'] == 'Bills'  # Highest single-category total


def test_get_summary_stats_no_expenses(app_context):
    # Create a new user with no expenses
    conn = db.get_db()
    cursor = conn.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('New User', 'new@test.com', 'hash')
    )
    conn.commit()
    new_user_id = cursor.lastrowid

    stats = queries.get_summary_stats(new_user_id)
    assert stats['total_spent'] == 0
    assert stats['transaction_count'] == 0
    assert stats['top_category'] == '—'


def test_get_recent_transactions_with_expenses(app_context):
    user_id = get_seed_user_id()
    assert user_id is not None

    transactions = queries.get_recent_transactions(user_id)
    assert len(transactions) == 8
    # Should be ordered newest first (by date DESC)
    assert transactions[0]['date'] == '2026-11-18'
    assert transactions[0]['description'] == 'Stationery and pens'
    assert transactions[0]['category'] == 'Other'
    assert transactions[0]['amount'] == 18.00
    assert transactions[-1]['date'] == '2026-11-01'


def test_get_recent_transactions_empty(app_context):
    conn = db.get_db()
    cursor = conn.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('New User', 'new2@test.com', 'hash')
    )
    conn.commit()
    new_user_id = cursor.lastrowid

    transactions = queries.get_recent_transactions(new_user_id)
    assert transactions == []


def test_get_category_breakdown_with_expenses(app_context):
    user_id = get_seed_user_id()
    assert user_id is not None

    categories = queries.get_category_breakdown(user_id)
    assert len(categories) == 7

    # Check structure
    for cat in categories:
        assert 'category' in cat
        assert 'total' in cat
        assert 'percentage' in cat
        assert isinstance(cat['percentage'], int)

    # Percentages should sum to 100
    pct_sum = sum(cat['percentage'] for cat in categories)
    assert pct_sum == 100

    # Should be ordered by total descending
    totals = [cat['total'] for cat in categories]
    assert totals == sorted(totals, reverse=True)

    # Check specific category totals match seed data
    cat_dict = {cat['category']: cat for cat in categories}
    assert cat_dict['Food']['total'] == 47.30
    assert cat_dict['Transport']['total'] == 45.00
    assert cat_dict['Bills']['total'] == 120.00
    assert cat_dict['Health']['total'] == 65.00
    assert cat_dict['Entertainment']['total'] == 55.00
    assert cat_dict['Shopping']['total'] == 89.99
    assert cat_dict['Other']['total'] == 18.00


def test_get_category_breakdown_empty(app_context):
    conn = db.get_db()
    cursor = conn.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('New User', 'new3@test.com', 'hash')
    )
    conn.commit()
    new_user_id = cursor.lastrowid

    categories = queries.get_category_breakdown(new_user_id)
    assert categories == []


# ============================================================
# Route tests for /profile
# ============================================================

def test_profile_unauthenticated():
    """Unauthenticated access to /profile should redirect to /login."""
    with app.test_client() as client:
        response = client.get('/profile', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location


def test_profile_seed_user(app_context):
    """Authenticated seed user should see their profile with real data."""
    with app.test_client() as client:
        # Login as seed user
        with client.session_transaction() as sess:
            user_id = get_seed_user_id()
            sess['user_id'] = user_id
            sess['user_name'] = 'Demo User'

        response = client.get('/profile')
        assert response.status_code == 200

        html = response.get_data(as_text=True)

        # Check user info
        assert 'Demo User' in html
        assert 'demo@spendly.com' in html
        assert 'November 2026' in html

        # Check summary stats
        assert '440.29' in html  # Total spent
        assert '8' in html       # Transaction count
        assert 'Bills' in html   # Top category

        # Check ₹ symbol appears
        assert '₹' in html

        # Check all 8 transactions appear
        for desc in [
            'Stationery and pens',
            'New running shoes',
            'Movie tickets and snacks',
            'Grocery shopping at local market',
            'Pharmacy prescription refill',
            'Electric utility bill',
            'Monthly subway pass',
            'Morning coffee and pastry'
        ]:
            assert desc in html

        # Check all 7 categories appear in breakdown
        for cat in ['Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other']:
            assert cat in html


def test_profile_new_user_no_expenses(app_context):
    """New user with no expenses should see empty states without errors."""
    with app.test_client() as client:
        # Create and login as new user
        conn = db.get_db()
        cursor = conn.execute(
            'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
            ('New User', 'new@test.com', 'hash')
        )
        conn.commit()
        new_user_id = cursor.lastrowid

        with client.session_transaction() as sess:
            sess['user_id'] = new_user_id
            sess['user_name'] = 'New User'

        response = client.get('/profile')
        assert response.status_code == 200

        html = response.get_data(as_text=True)

        # Should show zero totals
        assert '0.00' in html or '0' in html
        # Should not crash
        assert 'New User' in html
        assert 'new@test.com' in html