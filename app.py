from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash
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


@app.route("/login")
def login():
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
    return "Profile page — coming in Step 4"


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
