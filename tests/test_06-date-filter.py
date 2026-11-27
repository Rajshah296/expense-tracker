"""Tests for date filter on profile page (Step 6): query helpers and /profile route.

Covers:
- Unit tests for get_summary_stats, get_recent_transactions, get_category_breakdown
  with date_from/date_to filters
- Route tests for /profile with all 4 presets, custom ranges, invalid dates
- Edge cases: empty ranges, date_from > date_to, malformed params, auth guard
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app
import database.db as db
import database.queries as queries
from datetime import date, timedelta


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
# Unit tests for query helpers with date filters
# ============================================================

class TestGetSummaryStatsWithDateFilter:
    """Tests for get_summary_stats with date_from/date_to parameters."""

    def test_with_full_date_range_matching_all_seed_data(self, app_context):
        """All 8 seed expenses fall within November 2026."""
        user_id = get_seed_user_id()
        assert user_id is not None

        stats = queries.get_summary_stats(user_id, "2026-11-01", "2026-11-30")
        assert abs(stats['total_spent'] - 440.29) < 0.01
        assert stats['transaction_count'] == 8
        assert stats['top_category'] == 'Bills'

    def test_with_partial_date_range(self, app_context):
        """Filter to a subset of seed expenses (Entertainment + Shopping)."""
        user_id = get_seed_user_id()
        assert user_id is not None

        # 2026-11-12 (Entertainment) to 2026-11-15 (Shopping)
        stats = queries.get_summary_stats(user_id, "2026-11-12", "2026-11-15")
        assert abs(stats['total_spent'] - 144.99) < 0.01
        assert stats['transaction_count'] == 2
        assert stats['top_category'] == 'Shopping'

    def test_without_dates_backward_compatible(self, app_context):
        """Omitting dates behaves identically to Step 5 (no filter)."""
        user_id = get_seed_user_id()
        assert user_id is not None

        stats = queries.get_summary_stats(user_id)
        assert abs(stats['total_spent'] - 440.29) < 0.01
        assert stats['transaction_count'] == 8
        assert stats['top_category'] == 'Bills'

    def test_with_empty_date_range(self, app_context):
        """Date range with no matching expenses returns zeros."""
        user_id = get_seed_user_id()
        assert user_id is not None

        stats = queries.get_summary_stats(user_id, "2027-01-01", "2027-12-31")
        assert stats['total_spent'] == 0
        assert stats['transaction_count'] == 0
        assert stats['top_category'] == '—'

    def test_with_single_date_param_returns_all(self, app_context):
        """Providing only date_from or only date_to falls back to no filter (implementation uses AND)."""
        user_id = get_seed_user_id()
        assert user_id is not None

        # Only date_from - should not filter since both are required
        stats = queries.get_summary_stats(user_id, "2026-11-01", None)
        assert abs(stats['total_spent'] - 440.29) < 0.01
        assert stats['transaction_count'] == 8

        # Only date_to - should not filter
        stats = queries.get_summary_stats(user_id, None, "2026-11-30")
        assert abs(stats['total_spent'] - 440.29) < 0.01
        assert stats['transaction_count'] == 8


class TestGetRecentTransactionsWithDateFilter:
    """Tests for get_recent_transactions with date_from/date_to parameters."""

    def test_with_date_range_returns_matching_transactions(self, app_context):
        """Filter to 2026-11-12 to 2026-11-15 returns 2 transactions, newest first."""
        user_id = get_seed_user_id()
        assert user_id is not None

        transactions = queries.get_recent_transactions(
            user_id, date_from="2026-11-12", date_to="2026-11-15"
        )
        assert len(transactions) == 2
        assert transactions[0]['date'] == '2026-11-15'
        assert transactions[0]['category'] == 'Shopping'
        assert transactions[1]['date'] == '2026-11-12'
        assert transactions[1]['category'] == 'Entertainment'

    def test_without_dates_backward_compatible(self, app_context):
        """Omitting dates returns all 8 transactions newest first."""
        user_id = get_seed_user_id()
        assert user_id is not None

        transactions = queries.get_recent_transactions(user_id)
        assert len(transactions) == 8
        assert transactions[0]['date'] == '2026-11-18'
        assert transactions[-1]['date'] == '2026-11-01'

    def test_with_empty_date_range(self, app_context):
        """Date range with no expenses returns empty list."""
        user_id = get_seed_user_id()
        assert user_id is not None

        transactions = queries.get_recent_transactions(user_id, "2027-01-01", "2027-12-31")
        assert transactions == []

    def test_respects_limit_parameter(self, app_context):
        """Limit parameter still works with date filter."""
        user_id = get_seed_user_id()
        assert user_id is not None

        transactions = queries.get_recent_transactions(
            user_id, date_from="2026-11-01", date_to="2026-11-30", limit=3
        )
        assert len(transactions) == 3
        assert transactions[0]['date'] == '2026-11-18'


class TestGetCategoryBreakdownWithDateFilter:
    """Tests for get_category_breakdown with date_from/date_to parameters."""

    def test_with_date_range_returns_matching_categories(self, app_context):
        """Filter to 2026-11-12 to 2026-11-15 returns Entertainment + Shopping."""
        user_id = get_seed_user_id()
        assert user_id is not None

        categories = queries.get_category_breakdown(user_id, "2026-11-12", "2026-11-15")
        assert len(categories) == 2

        for cat in categories:
            assert 'category' in cat
            assert 'total' in cat
            assert 'percentage' in cat
            assert isinstance(cat['percentage'], int)

        pct_sum = sum(cat['percentage'] for cat in categories)
        assert pct_sum == 100

        totals = [cat['total'] for cat in categories]
        assert totals == sorted(totals, reverse=True)

        cat_dict = {cat['category']: cat for cat in categories}
        assert cat_dict['Shopping']['total'] == 89.99
        assert cat_dict['Entertainment']['total'] == 55.00

    def test_without_dates_backward_compatible(self, app_context):
        """Omitting dates returns all 7 categories with percentages summing to 100."""
        user_id = get_seed_user_id()
        assert user_id is not None

        categories = queries.get_category_breakdown(user_id)
        assert len(categories) == 7
        pct_sum = sum(cat['percentage'] for cat in categories)
        assert pct_sum == 100

    def test_with_empty_date_range(self, app_context):
        """Date range with no expenses returns empty list."""
        user_id = get_seed_user_id()
        assert user_id is not None

        categories = queries.get_category_breakdown(user_id, "2027-01-01", "2027-12-31")
        assert categories == []

    def test_percentages_sum_to_100_with_rounding_adjustment(self, app_context):
        """Percentage rounding adjustment works correctly within date range."""
        user_id = get_seed_user_id()
        assert user_id is not None

        categories = queries.get_category_breakdown(user_id, "2026-11-01", "2026-11-30")
        pct_sum = sum(cat['percentage'] for cat in categories)
        assert pct_sum == 100


# ============================================================
# Route tests for /profile with date filters
# ============================================================

class TestProfileRouteAuthGuard:
    """Authentication guard tests for /profile."""

    def test_unauthenticated_redirects_to_login(self, app_context):
        """Unauthenticated GET /profile redirects to /login."""
        with app.test_client() as client:
            response = client.get('/profile', follow_redirects=False)
            assert response.status_code == 302
            assert '/login' in response.location

    def test_unauthenticated_with_preset_redirects_to_login(self, app_context):
        """Unauthenticated access with preset param redirects to login."""
        with app.test_client() as client:
            response = client.get('/profile?preset=this-month', follow_redirects=False)
            assert response.status_code == 302
            assert '/login' in response.location

    def test_unauthenticated_with_custom_dates_redirects_to_login(self, app_context):
        """Unauthenticated access with custom dates redirects to login."""
        with app.test_client() as client:
            response = client.get('/profile?date_from=2026-11-01&date_to=2026-11-30', follow_redirects=False)
            assert response.status_code == 302
            assert '/login' in response.location


class TestProfileRoutePresets:
    """Tests for the four quick-select preset filters."""

    def _login_seed_user(self, client):
        """Helper to log in as the seeded demo user."""
        user_id = get_seed_user_id()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_name'] = 'Demo User'

    def test_no_filter_returns_all_data(self, app_context):
        """Visiting /profile with no query params shows all data (All Time)."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert 'Demo User' in html
            assert '440.29' in html
            assert '8' in html
            assert 'Bills' in html

    def test_this_month_preset(self, app_context):
        """'This Month' preset filters to current calendar month."""
        with app.test_client() as client:
            self._login_seed_user(client)

            # All seed data is in November 2026; "This Month" (Nov 2026) should show all
            response = client.get('/profile?preset=this-month')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html
            assert '8' in html

    def test_last_3_months_preset(self, app_context):
        """'Last 3 Months' preset filters to 3-month window ending today."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?preset=last-3-months')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html

    def test_last_6_months_preset(self, app_context):
        """'Last 6 Months' preset filters to 6-month window ending today."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?preset=last-6-months')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html

    def test_all_time_preset(self, app_context):
        """'All Time' preset removes filter and shows all expenses."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?preset=all-time')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html
            assert '8' in html


class TestProfileRouteCustomDateRange:
    """Tests for custom date range filtering via date_from/date_to."""

    def _login_seed_user(self, client):
        user_id = get_seed_user_id()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_name'] = 'Demo User'

    def test_valid_custom_range_filters_correctly(self, app_context):
        """Custom date_from/date_to filters all three sections correctly."""
        with app.test_client() as client:
            self._login_seed_user(client)

            # 2026-11-12 (Entertainment) to 2026-11-15 (Shopping)
            response = client.get('/profile?date_from=2026-11-12&date_to=2026-11-15')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '144.99' in html
            assert 'Entertainment' in html
            assert 'Shopping' in html
            # These should NOT appear in this date range
            assert 'Bills' not in html
            assert 'Food' not in html
            assert 'Transport' not in html

    def test_custom_range_including_all_data(self, app_context):
        """Custom range covering all seed data returns all expenses."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?date_from=2026-11-01&date_to=2026-11-30')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html
            assert '8' in html


class TestProfileRouteInvalidDates:
    """Tests for malformed/invalid date parameter handling."""

    def _login_seed_user(self, client):
        user_id = get_seed_user_id()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_name'] = 'Demo User'

    def test_malformed_date_from_falls_back_to_all_time(self, app_context):
        """Invalid date_from falls back to unfiltered view silently."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?date_from=not-a-date&date_to=2026-11-30')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html
            assert '8' in html

    def test_malformed_date_to_falls_back_to_all_time(self, app_context):
        """Invalid date_to falls back to unfiltered view silently."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?date_from=2026-11-01&date_to=not-a-date')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html
            assert '8' in html

    def test_both_dates_malformed_falls_back_to_all_time(self, app_context):
        """Both dates malformed falls back to unfiltered view."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?date_from=bad&date_to=worse')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html

    def test_date_from_after_date_to_shows_flash_error(self, app_context):
        """date_from > date_to shows flash error and falls back to unfiltered view."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?date_from=2026-11-30&date_to=2026-11-01')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert 'Start date must be before end date' in html
            # Falls back to all time
            assert '440.29' in html
            assert '8' in html

    def test_date_from_equals_date_to_is_valid(self, app_context):
        """date_from == date_to is a valid single-day range."""
        with app.test_client() as client:
            self._login_seed_user(client)

            # Single day with one expense (2026-11-18: Other - Stationery)
            response = client.get('/profile?date_from=2026-11-18&date_to=2026-11-18')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '18.00' in html
            assert 'Other' in html
            assert 'Stationery and pens' in html


class TestProfileRouteEmptyState:
    """Tests for empty state when user has no expenses in date range."""

    def test_new_user_with_filter_shows_empty_state(self, app_context):
        """New user with no expenses shows zeros/empty states with any filter."""
        with app.test_client() as client:
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

            response = client.get('/profile?date_from=2026-11-01&date_to=2026-11-30')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert 'New User' in html
            assert 'new@test.com' in html
            # Should show zero total
            assert '0.00' in html or '0' in html
            # Should show empty transaction message (template-specific text)
            assert 'No transactions' in html or 'No expenses' in html or 'empty' in html.lower()

    def test_existing_user_with_future_date_range_shows_empty(self, app_context):
        """Existing user with future date range sees empty state."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?date_from=2027-01-01&date_to=2027-12-31')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '0.00' in html or '0' in html
            assert 'No transactions' in html or 'No expenses' in html or 'empty' in html.lower()

    def _login_seed_user(self, client):
        user_id = get_seed_user_id()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_name'] = 'Demo User'


class TestProfileRouteEdgeCases:
    """Additional edge cases and boundary conditions."""

    def _login_seed_user(self, client):
        user_id = get_seed_user_id()
        with client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_name'] = 'Demo User'

    def test_preset_overrides_manual_dates(self, app_context):
        """Preset parameter takes precedence over manual date_from/date_to."""
        with app.test_client() as client:
            self._login_seed_user(client)

            # Provide both preset and manual dates; preset should win
            response = client.get('/profile?preset=this-month&date_from=2020-01-01&date_to=2020-12-31')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            # Should show November 2026 data (this-month), not 2020 data
            assert '440.29' in html

    def test_invalid_preset_falls_back_to_all_time(self, app_context):
        """Unknown preset value falls back to all time."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?preset=invalid-preset')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            assert '440.29' in html

    def test_currency_symbol_appears_regardless_of_filter(self, app_context):
        """₹ symbol appears in all filtered views."""
        with app.test_client() as client:
            self._login_seed_user(client)

            for params in [
                '',
                '?preset=this-month',
                '?preset=last-3-months',
                '?preset=last-6-months',
                '?preset=all-time',
                '?date_from=2026-11-12&date_to=2026-11-15',
            ]:
                response = client.get(f'/profile{params}')
                assert response.status_code == 200
                html = response.get_data(as_text=True)
                assert '₹' in html, f"Missing ₹ symbol for params: {params}"

    def test_all_sections_filtered_consistently(self, app_context):
        """Summary stats, transactions, and categories all respect the same filter."""
        with app.test_client() as client:
            self._login_seed_user(client)

            # Filter to just 2026-11-15 (Shopping only)
            response = client.get('/profile?date_from=2026-11-15&date_to=2026-11-15')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            # All three sections should reflect only Shopping (89.99)
            assert '89.99' in html
            assert 'Shopping' in html
            # Other categories should not appear
            assert 'Bills' not in html
            assert 'Food' not in html
            assert 'Transport' not in html
            assert 'Health' not in html
            assert 'Entertainment' not in html
            assert 'Other' not in html

    def test_active_preset_highlighted_in_response(self, app_context):
        """Active preset is passed to template for UI highlighting."""
        with app.test_client() as client:
            self._login_seed_user(client)

            # Test each preset produces a response that includes its label
            presets = {
                'this-month': 'This Month',
                'last-3-months': 'Last 3 Months',
                'last-6-months': 'Last 6 Months',
                'all-time': 'All Time',
            }

            for preset_key, preset_label in presets.items():
                response = client.get(f'/profile?preset={preset_key}')
                assert response.status_code == 200
                html = response.get_data(as_text=True)
                # The filter label should appear in the response
                assert preset_label in html

    def test_custom_range_active_state_shows_date_values(self, app_context):
        """Custom range shows the selected dates in the UI."""
        with app.test_client() as client:
            self._login_seed_user(client)

            response = client.get('/profile?date_from=2026-11-10&date_to=2026-11-20')
            assert response.status_code == 200

            html = response.get_data(as_text=True)
            # Custom range label should include the dates
            assert '2026-11-10' in html
            assert '2026-11-20' in html
            # Or "Custom" label
            assert 'Custom' in html or 'custom' in html.lower()