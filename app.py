from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, close_db, init_db, seed_db, get_user_by_email, create_user
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown
from datetime import datetime, timedelta

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


def _parse_date(date_str: str):
    """Parse ISO date string, return None if invalid."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def _compute_preset_dates(preset: str):
    """Compute date_from and date_to for a given preset."""
    today = datetime.now().date()

    if preset == "this-month":
        # First day of current month to today
        date_from = today.replace(day=1)
        date_to = today
    elif preset == "last-3-months":
        # 3 months ago to today
        date_from = today - timedelta(days=90)
        date_to = today
    elif preset == "last-6-months":
        # 6 months ago to today
        date_from = today - timedelta(days=180)
        date_to = today
    elif preset == "all-time":
        return None, None
    else:
        return None, None

    return date_from.isoformat(), date_to.isoformat()


@app.route("/profile")
def profile():
    # Authentication guard
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Fetch real data from database
    user = get_user_by_id(user_id)
    if user is None:
        # User not found — clear session and redirect to login
        session.clear()
        return redirect(url_for("login"))

    # Handle date filtering
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))
    preset = request.args.get("preset")

    # If preset is provided, compute dates from preset (overrides manual dates)
    if preset and preset in ("this-month", "last-3-months", "last-6-months", "all-time"):
        date_from, date_to = _compute_preset_dates(preset)

    # Validate date range
    active_preset = "all-time"
    if date_from and date_to:
        if date_from > date_to:
            flash("Start date must be before end date.")
            date_from = None
            date_to = None
        else:
            # Determine active preset for UI highlighting
            if preset:
                active_preset = preset
            else:
                active_preset = "custom"
    elif preset == "all-time":
        active_preset = "all-time"
        date_from = None
        date_to = None
    else:
        active_preset = "all-time"
        date_from = None
        date_to = None

    # Convert date objects to strings for query helpers
    date_from_str = date_from if isinstance(date_from, str) else (date_from.isoformat() if date_from else None)
    date_to_str = date_to if isinstance(date_to, str) else (date_to.isoformat() if date_to else None)

    summary = get_summary_stats(user_id, date_from_str, date_to_str)
    transactions = get_recent_transactions(user_id, date_from=date_from_str, date_to=date_to_str)
    categories = get_category_breakdown(user_id, date_from_str, date_to_str)

    # Preset URLs for filter bar
    preset_urls = {
        "this-month": url_for("profile", preset="this-month"),
        "last-3-months": url_for("profile", preset="last-3-months"),
        "last-6-months": url_for("profile", preset="last-6-months"),
        "all-time": url_for("profile", preset="all-time"),
    }

    # Human-readable filter label
    filter_labels = {
        "this-month": "This Month",
        "last-3-months": "Last 3 Months",
        "last-6-months": "Last 6 Months",
        "all-time": "All Time",
        "custom": f"Custom ({date_from_str} to {date_to_str})" if date_from_str and date_to_str else "All Time"
    }

    return render_template(
        "profile.html",
        user=user,
        summary=summary,
        transactions=transactions,
        categories=categories,
        active_preset=active_preset,
        preset_urls=preset_urls,
        filter_labels=filter_labels,
        date_from=date_from_str,
        date_to=date_to_str
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
