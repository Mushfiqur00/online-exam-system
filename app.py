from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secretkey"

# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# LOGIN
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Fixed credentials
        if username == "teacher" and password == "1234":
            session["role"] = "admin"
            return redirect("/admin-dashboard")

        elif username == "student" and password == "group4":
            session["role"] = "student"
            return redirect("/student-dashboard")

        else:
            return "Invalid Credentials"

    return render_template("login.html")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    exams = conn.execute("""
        SELECT * FROM exams
        ORDER BY exam_date ASC, start_time ASC
    """).fetchall()

    conn.close()

    return render_template("admin_dashboard.html", exams=exams)


# -----------------------------
# CREATE EXAM
# -----------------------------
@app.route("/create-exam", methods=["POST"])
def create_exam():
    if session.get("role") != "admin":
        return redirect("/")

    title = request.form.get("title")
    exam_date = request.form.get("exam_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    duration = request.form.get("duration")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO exams (title, exam_date, start_time, end_time, duration)
        VALUES (?, ?, ?, ?, ?)
    """, (title, exam_date, start_time, end_time, duration))

    conn.commit()
    conn.close()

    return redirect("/admin-dashboard")


# -----------------------------
# DELETE EXAM
# -----------------------------
@app.route("/delete-exam/<int:exam_id>")
def delete_exam(exam_id):
    if session.get("role") != "admin":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
    conn.commit()
    conn.close()

    return redirect("/admin-dashboard")


# -----------------------------
# STUDENT DASHBOARD
# -----------------------------
@app.route("/student-dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    exams = conn.execute("""
        SELECT * FROM exams
        ORDER BY exam_date ASC, start_time ASC
    """).fetchall()

    conn.close()

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    return render_template(
        "student_dashboard.html",
        exams=exams,
        today=today,
        current_time=current_time
    )
# -----------------------------
# START EXAM (Eligibility Check)
# -----------------------------
@app.route("/start-exam/<int:exam_id>")
def start_exam(exam_id):
    if session.get("role") != "student":
        return redirect("/")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row

    exam = conn.execute(
        "SELECT * FROM exams WHERE id = ?",
        (exam_id,)
    ).fetchone()

    conn.close()

    if exam is None:
        return "Exam not found"

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    # Date check
    if today < exam["exam_date"]:
        return "Exam has not started yet"

    if today > exam["exam_date"]:
        return "Exam date is over"

    # Time check
    if current_time < exam["start_time"]:
        return "Exam has not started yet"

    if current_time > exam["end_time"]:
        return "Exam time is over"

    return "Exam Started Successfully"


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)