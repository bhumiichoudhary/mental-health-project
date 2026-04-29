from flask import Flask, render_template, request, redirect, session
import sqlite3
import numpy as np
import pickle
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

model = pickle.load(open("model.pkl", "rb"))

# DATABASE SETUP
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY,
        username TEXT,
        score INTEGER,
        result TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (u,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], p):
            session["user"] = u
            return redirect("/dashboard")
        else:
            return "Invalid login"

    return render_template("login.html")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        hashed = generate_password_hash(p)

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (NULL,?,?)", (u, hashed))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# PREDICTION
@app.route("/predict", methods=["POST"])
def predict():
    data = request.form

    gad = sum(int(data[f"gad{i}"]) for i in range(7))
    phq = sum(int(data[f"phq{i}"]) for i in range(9))

    sleep = float(data["sleep"])
    screen = float(data["screen"])
    exercise = float(data["exercise"])

    score = gad + phq

    if score < 10:
        result = "Low Risk"
    elif score < 20:
        result = "Moderate Risk"
    else:
        result = "High Risk"

    tips = []

    if sleep < 6:
        tips.append("Increase sleep to 7-8 hours")
    if screen > 6:
        tips.append("Reduce screen time")
    if exercise < 2:
        tips.append("Exercise regularly")
    if gad > 10:
        tips.append("Practice meditation")
    if phq > 10:
        tips.append("Talk to someone you trust")

    if not tips:
        tips.append("You are doing well. Keep it up!")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO history VALUES (NULL,?,?,?)",
              (session["user"], score, result))
    conn.commit()
    conn.close()

    return render_template("result.html", result=result, tips=tips)

# HISTORY
@app.route("/history")
def history():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT score FROM history WHERE username=?", (session["user"],))
    data = c.fetchall()
    conn.close()

    scores = [x[0] for x in data]
    return render_template("history.html", scores=scores)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# RUN APP
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)