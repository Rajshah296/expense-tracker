from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, close_db, init_db, seed_db, get_user_by_email, create_user

app = Flask(__name__)
app.secret_key = 'dev-secret-change-in-production'

app.teardown_appcontext(close_db)

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Redirect logged-in users to landing page
    if "user_id" in session:
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validation
        if not name or not email or not password:
            return render_template("register.html", error="All fields are required")
        if "@" not in email or "." not in email:
            return render_template("register.html", error="Invalid email format")
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters")

        # Check duplicate email
        if get_user_by_email(email):
            return render_template("register.html", error="Email already registered")

        # Create user
        password_hash = generate_password_hash(password)
        user_id = create_user(name, email, password_hash)

        # Start session
        session["user_id"] = user_id
        session["user_name"] = name

        flash("Account created successfully!")
        return redirect(url_for("profile"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # Redirect logged-in users to landing page
    if "user_id" in session:
        return redirect(url_for("landing"))

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


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    # Authentication guard
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Hardcoded user info (in Step 5 this will come from DB)
    user = {
        "name": session.get("user_name", "Demo User"),
        "email": "demo@spendly.com",
        "member_since": "November 2026",
        "initials": session.get("user_name", "Demo User")[0].upper()
    }

    # Hardcoded summary stats
    summary = {
        "total_spent": 440.29,
        "transaction_count": 8,
        "top_category": "Food"
    }

    # Hardcoded transaction history (matches seed_db data)
    transactions = [
        {"date": "2026-11-18", "description": "Stationery and pens", "category": "Other", "amount": 18.00},
        {"date": "2026-11-15", "description": "New running shoes", "category": "Shopping", "amount": 89.99},
        {"date": "2026-11-12", "description": "Movie tickets and snacks", "category": "Entertainment", "amount": 55.00},
        {"date": "2026-11-10", "description": "Grocery shopping at local market", "category": "Food", "amount": 32.80},
        {"date": "2026-11-08", "description": "Pharmacy prescription refill", "category": "Health", "amount": 65.00},
        {"date": "2026-11-05", "description": "Electric utility bill", "category": "Bills", "amount": 120.00},
        {"date": "2026-11-03", "description": "Monthly subway pass", "category": "Transport", "amount": 45.00},
        {"date": "2026-11-01", "description": "Morning coffee and pastry", "category": "Food", "amount": 14.50},
    ]

    # Hardcoded category breakdown (totals from seed data)
    categories = [
        {"category": "Food", "total": 47.30, "percentage": 11},
        {"category": "Transport", "total": 45.00, "percentage": 10},
        {"category": "Bills", "total": 120.00, "percentage": 27},
        {"category": "Health", "total": 65.00, "percentage": 15},
        {"category": "Entertainment", "total": 55.00, "percentage": 12},
        {"category": "Shopping", "total": 89.99, "percentage": 20},
        {"category": "Other", "total": 18.00, "percentage": 4},
    ]

    return render_template(
        "profile.html",
        user=user,
        summary=summary,
        transactions=transactions,
        categories=categories
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
