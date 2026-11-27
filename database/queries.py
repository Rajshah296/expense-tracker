"""Pure query helpers for the profile page — no Flask imports."""

from database.db import get_db
from datetime import datetime


def get_user_by_id(user_id: int):
    """Fetch user profile info by ID.

    Returns:
        dict with keys: name, email, member_since, initials
        or None if user not found
    """
    db = get_db()
    row = db.execute(
        'SELECT name, email, created_at FROM users WHERE id = ?',
        (user_id,)
    ).fetchone()

    if row is None:
        return None

    # Parse created_at and format as "Month YYYY"
    try:
        created = datetime.fromisoformat(row['created_at'])
        member_since = created.strftime('%B %Y')
    except (ValueError, TypeError):
        member_since = 'Unknown'

    return {
        'name': row['name'],
        'email': row['email'],
        'member_since': member_since,
        'initials': row['name'][0].upper() if row['name'] else 'U'
    }


def get_summary_stats(user_id: int):
    """Compute summary statistics for a user.

    Returns:
        dict with keys: total_spent (float), transaction_count (int), top_category (str)
    """
    db = get_db()
    row = db.execute('''
        SELECT
            COALESCE(SUM(amount), 0) as total_spent,
            COUNT(*) as transaction_count
        FROM expenses WHERE user_id = ?
    ''', (user_id,)).fetchone()

    total_spent = row['total_spent'] or 0.0
    transaction_count = row['transaction_count'] or 0

    # Find top category by total amount
    top_category_row = db.execute('''
        SELECT category
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        LIMIT 1
    ''', (user_id,)).fetchone()

    top_category = top_category_row['category'] if top_category_row else '—'

    return {
        'total_spent': total_spent,
        'transaction_count': transaction_count,
        'top_category': top_category
    }


def get_recent_transactions(user_id: int, limit: int = 10):
    """Fetch recent transactions for a user, newest first.

    Returns:
        List of dicts with keys: date, description, category, amount
    """
    db = get_db()
    rows = db.execute('''
        SELECT date, description, category, amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC, created_at DESC
        LIMIT ?
    ''', (user_id, limit)).fetchall()

    return [
        {
            'date': row['date'],
            'description': row['description'] or '',
            'category': row['category'],
            'amount': row['amount']
        }
        for row in rows
    ]


def get_category_breakdown(user_id: int):
    """Get per-category breakdown with percentages.

    Returns:
        List of dicts with keys: category, total, percentage (int)
        Ordered by total descending. Percentages sum to 100.
    """
    db = get_db()
    rows = db.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id,)).fetchall()

    if not rows:
        return []

    # Convert to list of dicts and compute total
    categories = [{'category': row['category'], 'total': row['total']} for row in rows]
    total = sum(c['total'] for c in categories)

    if total == 0:
        return []

    # Compute raw percentages
    for c in categories:
        c['pct_raw'] = (c['total'] / total) * 100

    # Round to integers
    for c in categories:
        c['percentage'] = round(c['pct_raw'])

    # Adjust largest category to absorb rounding difference
    pct_sum = sum(c['percentage'] for c in categories)
    if pct_sum != 100 and categories:
        diff = 100 - pct_sum
        categories[0]['percentage'] += diff

    # Return clean dicts with expected keys
    return [
        {'category': c['category'], 'total': c['total'], 'percentage': c['percentage']}
        for c in categories
    ]