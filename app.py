from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-development-key-change-before-deployment")
# On hosting, set DB_PATH to a persistent disk location (configured in render.yaml).
DB = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "digital_literacy.db"))

QUIZ = [
    ("Which is the safest way to create a password?", ["Use your name and birth year", "Use a long unique password", "Use 12345678", "Use your phone number"], 1),
    ("What should you do before clicking an unknown link?", ["Click immediately", "Share it with friends", "Check the sender and link", "Enter your OTP"], 2),
    ("What is OTP?", ["One-Time Password", "Online Transfer Payment", "Open Text Program", "Official Transaction Page"], 0),
    ("Should you share an OTP with another person?", ["Yes", "Only on social media", "Only if they sound trustworthy", "No"], 3),
    ("Which is an example of a digital government service?", ["Online certificate application", "Paper notebook", "Village notice board", "Printed newspaper"], 0),
    ("What does UPI allow?", ["Digital payments", "Only phone calls", "Printing documents", "Changing a SIM physically"], 0),
    ("What should you do if you receive a suspicious banking message?", ["Reply with your PIN", "Ignore/check through the official bank channel", "Forward your OTP", "Send your password"], 1),
    ("Which information should generally be kept private?", ["OTP and PIN", "Public website address", "School subject", "Weather"], 0),
    ("What is digital literacy?", ["Ability to safely and effectively use digital technologies", "Only knowing how to type", "Only using social media", "Repairing computers"], 0),
    ("Before installing an app, you should preferably:", ["Check its source and permissions", "Give it every permission", "Download from random links", "Share your password"], 0),
]

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        age INTEGER,
        location TEXT,
        education TEXT,
        skill_level TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        level TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        age = request.form.get("age") or None
        location = request.form.get("location", "").strip()
        education = request.form.get("education", "").strip()
        skill_level = request.form.get("skill_level", "Beginner")

        if not name or not email or len(password) < 6:
            flash("Please enter valid details. Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (name,email,password_hash,age,location,education,skill_level) VALUES (?,?,?,?,?,?,?)",
                (name, email, generate_password_hash(password), age, location, education, skill_level)
            )
            conn.commit()
            flash("Registration successful. You can now log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "error")
            return redirect(url_for("register"))
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    results = conn.execute(
        "SELECT * FROM quiz_results WHERE user_id=? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", user=user, results=results)

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "user_id" not in session:
        flash("Please log in before taking the quiz.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        score = 0
        for i, (_, _, answer) in enumerate(QUIZ):
            if request.form.get(f"q{i}") == str(answer):
                score += 1

        if score >= 8:
            level = "Advanced"
        elif score >= 5:
            level = "Intermediate"
        else:
            level = "Beginner"

        conn = get_db()
        conn.execute(
            "INSERT INTO quiz_results (user_id,score,total,level) VALUES (?,?,?,?)",
            (session["user_id"], score, len(QUIZ), level)
        )
        conn.commit()
        conn.close()
        return render_template("quiz_result.html", score=score, total=len(QUIZ), level=level)

    return render_template("quiz.html", questions=QUIZ)

@app.route("/resources")
def resources():
    return render_template("resources.html")

@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        message = request.form["message"].strip()
        user_id = session.get("user_id")
        if message:
            conn = get_db()
            conn.execute("INSERT INTO feedback (user_id,name,message) VALUES (?,?,?)",
                         (user_id, name, message))
            conn.commit()
            conn.close()
            flash("Thank you for your feedback.", "success")
        return redirect(url_for("feedback"))
    return render_template("feedback.html")

# Demo admin login: /admin/login
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
        if request.form["username"] == admin_username and request.form["password"] == admin_password:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    conn = get_db()
    users = conn.execute("SELECT id,name,email,age,location,education,skill_level,created_at FROM users ORDER BY created_at DESC").fetchall()
    results = conn.execute("""
        SELECT quiz_results.*, users.name, users.email
        FROM quiz_results JOIN users ON users.id=quiz_results.user_id
        ORDER BY quiz_results.created_at DESC
    """).fetchall()
    feedback_rows = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin.html", users=users, results=results, feedback=feedback_rows)

# Initialize tables when the app starts under either Flask or Gunicorn.
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
