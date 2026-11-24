#!/usr/bin/env python3
"""
Seed a realistic Indian user into the Spendly database.
"""
import sqlite3
import random
from datetime import datetime
from werkzeug.security import generate_password_hash

DATABASE = 'spendly.db'

# Realistic Indian first names (mixed regions)
FIRST_NAMES = [
    # North Indian
    'Arjun', 'Rahul', 'Amit', 'Vikram', 'Sanjay', 'Rajesh', 'Ankit', 'Nikhil', 'Manish', 'Deepak',
    'Priya', 'Neha', 'Anjali', 'Pooja', 'Swati', 'Kavya', 'Meera', 'Shreya', 'Divya', 'Riya',
    # South Indian
    'Arvind', 'Karthik', 'Suresh', 'Ganesh', 'Ramesh', 'Venkatesh', 'Balaji', 'Srinivas', 'Prakash', 'Mohan',
    'Lakshmi', 'Priyanka', 'Deepa', 'Anitha', 'Shalini', 'Nandini', 'Meenakshi', 'Kavitha', 'Sowmya', 'Vidya',
    # East Indian
    'Subham', 'Sourav', 'Anirban', 'Debjit', 'Arnab', 'Sayan', 'Koushik', 'Ritwik', 'Ankan', 'Avik',
    'Sneha', 'Taniya', 'Riya', 'Ananya', 'Payel', 'Moumita', 'Sohini', 'Debolina', 'Shruti', 'Ishita',
    # West Indian
    'Harsh', 'Yash', 'Karan', 'Jay', 'Meet', 'Dhruv', 'Parth', 'Viraj', 'Om', 'Dev',
    'Aisha', 'Diya', 'Myra', 'Kiara', 'Anaya', 'Ira', 'Nitya', 'Riya', 'Tara', 'Zara',
]

# Realistic Indian last names (mixed regions)
LAST_NAMES = [
    'Sharma', 'Verma', 'Gupta', 'Singh', 'Kumar', 'Jain', 'Agarwal', 'Mishra', 'Tiwari', 'Pandey',
    'Reddy', 'Nair', 'Iyer', 'Menon', 'Pillai', 'Rao', 'Krishnan', 'Subramaniam', 'Venkataraman', 'Gopalan',
    'Banerjee', 'Chatterjee', 'Mukherjee', 'Ghosh', 'Das', 'Roy', 'Chakraborty', 'Bhattacharya', 'Sengupta', 'Pal',
    'Patel', 'Shah', 'Desai', 'Mehta', 'Joshi', 'Trivedi', 'Dave', 'Vyas', 'Thakkar', 'Modi',
]

EMAIL_DOMAINS = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']


def generate_indian_name():
    """Generate a realistic Indian full name."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"


def generate_email(name):
    """Generate email from name with random number suffix."""
    # Convert to lowercase, replace spaces with dots
    base = name.lower().replace(' ', '.')
    # Add random 2-3 digit number
    suffix = random.randint(10, 999)
    domain = random.choice(EMAIL_DOMAINS)
    return f"{base}{suffix}@{domain}"


def get_db():
    """Get database connection (same pattern as db.py)."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    return db


def email_exists(db, email):
    """Check if email already exists in users table."""
    cursor = db.execute('SELECT 1 FROM users WHERE email = ?', (email,))
    return cursor.fetchone() is not None


def insert_user(db, name, email, password_hash):
    """Insert user into database and return the user ID."""
    cursor = db.execute(
        'INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)',
        (name, email, password_hash, datetime.now().isoformat())
    )
    db.commit()
    return cursor.lastrowid


def main():
    # Initialize database tables
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
    db.commit()

    # Generate unique user
    password_hash = generate_password_hash('password123')
    max_attempts = 10

    for attempt in range(max_attempts):
        name = generate_indian_name()
        email = generate_email(name)

        if not email_exists(db, email):
            user_id = insert_user(db, name, email, password_hash)
            print(f"id: {user_id}")
            print(f"name: {name}")
            print(f"email: {email}")
            db.close()
            return

        print(f"Attempt {attempt + 1}: Email {email} already exists, retrying...")

    # Fallback: use timestamp to guarantee uniqueness
    name = generate_indian_name()
    email = f"{name.lower().replace(' ', '.')}{int(datetime.now().timestamp())}@gmail.com"
    user_id = insert_user(db, name, email, password_hash)
    print(f"id: {user_id}")
    print(f"name: {name}")
    print(f"email: {email}")
    db.close()


if __name__ == '__main__':
    main()