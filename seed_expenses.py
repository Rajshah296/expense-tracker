#!/usr/bin/env python3
"""
Seed realistic dummy expenses for a specific user.
Usage: python seed_expenses.py <user_id> <count> <months>
"""
import sys
import sqlite3
import random
from datetime import datetime, timedelta

DATABASE = 'spendly.db'

def get_db():
    """Get database connection (same pattern as db.py but without Flask g)."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    return db

# Categories with realistic Indian descriptions and amount ranges (₹)
CATEGORIES = {
    'Food': {
        'weight': 30,
        'amount_range': (50, 800),
        'descriptions': [
            'Lunch at local restaurant',
            'Grocery shopping at Big Bazaar',
            'Dinner with friends',
            'Street food - vada pav and chai',
            'Weekend brunch at cafe',
            'Food delivery - Swiggy/Zomato',
            'Tiffin service monthly',
            'Snacks and beverages',
            'Festival sweets and snacks',
            'Office canteen meals',
        ]
    },
    'Transport': {
        'weight': 20,
        'amount_range': (20, 500),
        'descriptions': [
            'Auto rickshaw fare',
            'Metro monthly pass',
            'Bus pass renewal',
            'Cab to airport',
            'Petrol for scooter',
            'Uber/Ola ride',
            'Local train pass',
            'Parking charges',
            'Inter-city bus ticket',
            'Bike service',
        ]
    },
    'Bills': {
        'weight': 15,
        'amount_range': (200, 3000),
        'descriptions': [
            'Electricity bill - BESCOM/TNEB',
            'Water bill',
            'Internet broadband - Jio/Airtel',
            'Mobile postpaid bill',
            'Gas cylinder refill',
            'Society maintenance charges',
            'DTH/cable TV recharge',
            'Property tax',
            'Insurance premium',
            'Credit card bill',
        ]
    },
    'Health': {
        'weight': 8,
        'amount_range': (100, 2000),
        'descriptions': [
            'Pharmacy - medicines',
            'Doctor consultation fee',
            'Diagnostic lab tests',
            'Dental checkup',
            'Eye checkup and glasses',
            'Physiotherapy session',
            'Health checkup package',
            'Vaccination',
            'Ayurvedic consultation',
            'Medical insurance copay',
        ]
    },
    'Entertainment': {
        'weight': 8,
        'amount_range': (100, 1500),
        'descriptions': [
            'Movie tickets - PVR/INOX',
            'OTT subscription - Netflix/Prime',
            'Concert/event tickets',
            'Amusement park',
            'Bowling/gaming zone',
            'Streaming service renewal',
            'Book purchase',
            'Magazine subscription',
            'Standup comedy show',
            'Museum entry',
        ]
    },
    'Shopping': {
        'weight': 12,
        'amount_range': (200, 5000),
        'descriptions': [
            'Clothes - ethnic wear',
            'Footwear - sneakers/sandals',
            'Electronics - phone accessories',
            'Home decor items',
            'Kitchen appliances',
            'Beauty/cosmetic products',
            'Books and stationery',
            'Gifts for family',
            'Furniture',
            'Online shopping - Amazon/Flipkart',
        ]
    },
    'Other': {
        'weight': 7,
        'amount_range': (50, 1000),
        'descriptions': [
            'Temple donation',
            'Charity contribution',
            'Pet care - vet/food',
            'Plant nursery',
            'Car wash/detailing',
            'Laundry/dry cleaning',
            'Salon/parlour',
            'Newspaper subscription',
            'Courier/postage',
            'Miscellaneous expenses',
        ]
    },
}


def pick_category():
    """Pick a category based on weights."""
    categories = list(CATEGORIES.keys())
    weights = [CATEGORIES[c]['weight'] for c in categories]
    return random.choices(categories, weights=weights, k=1)[0]


def generate_random_date(months_back):
    """Generate a random date within the past N months."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime('%Y-%m-%d')


def main():
    if len(sys.argv) != 4:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
    except ValueError:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

    # Use the same db connection pattern as db.py
    db = get_db()

    # Verify user exists
    cursor = db.execute('SELECT id FROM users WHERE id = ?', (user_id,))
    if not cursor.fetchone():
        print(f"No user found with id {user_id}.")
        db.close()
        sys.exit(1)

    # Generate expenses
    expenses = []
    for _ in range(count):
        category = pick_category()
        cat_info = CATEGORIES[category]
        amount = round(random.uniform(*cat_info['amount_range']), 2)
        description = random.choice(cat_info['descriptions'])
        date = generate_random_date(months)

        expenses.append((user_id, amount, category, date, description))

    # Insert all in a single transaction
    try:
        db.executemany(
            'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
            expenses
        )
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error inserting expenses: {e}")
        db.close()
        sys.exit(1)

    # Print confirmation
    print(f"Inserted {count} expenses for user {user_id}")

    # Date range
    dates = [e[3] for e in expenses]
    print(f"Date range: {min(dates)} to {max(dates)}")

    # Sample of 5 inserted records
    print("\nSample of inserted records:")
    cursor = db.execute('''
        SELECT id, amount, category, date, description
        FROM expenses
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    ''', (user_id,))
    for row in cursor.fetchall():
        print(f"  id={row[0]}, amount=₹{row[1]:.2f}, category={row[2]}, date={row[3]}, description={row[4]}")

    db.close()


if __name__ == '__main__':
    main()