from flask import Flask, render_template, request, redirect, session
from datetime import datetime
from models import db, Exam

app = Flask(__name__)

# SECRET KEY
app.secret_key = "secretkey"

# DATABASE CONFIG
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# CREATE DATABASE
with app.app_context():
    db.create_all()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "teacher" and password == "1234":
            session["role"] = "admin"
            return redirect("/admin-dashboard")

        elif username == "student" and password == "group4":
            session["role"] = "student"
            session["username"] = "student"
            session["group"] = "group4"
            return redirect("/student-dashboard")

        else:
            return "Invalid Credentials"

    return render_template("login.html")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin-dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect("/")

    exams = Exam.query.order_by(Exam.exam_date.asc()).all()
    return render_template("admin_dashboard.html", exams=exams)


# ---------------- CREATE EXAM ----------------
@app.route("/create-exam", methods=["POST"])
def create_exam():
    if session.get("role") != "admin":
        return redirect("/")

    new_exam = Exam(
        title=request.form["title"],
        exam_date=request.form["exam_date"],
        start_time=request.form["start_time"],
        end_time=request.form["end_time"],
        duration=request.form["duration"],
        assigned_to=request.form["assigned_to"]
    )

    db.session.add(new_exam)
    db.session.commit()

    return redirect("/admin-dashboard")


# ---------------- DELETE EXAM ----------------
@app.route("/delete-exam/<int:exam_id>")
def delete_exam(exam_id):
    if session.get("role") != "admin":
        return redirect("/")

    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()

    return redirect("/admin-dashboard")


# ---------------- STUDENT DASHBOARD ----------------
@app.route("/student-dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect("/")

    username = session.get("username")
    group = session.get("group")

    exams = Exam.query.filter(
        (Exam.assigned_to == username) |
        (Exam.assigned_to == group)
    ).order_by(Exam.exam_date.asc()).all()

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    upcoming = []
    ongoing = []
    completed = []

    for exam in exams:
        if exam.exam_date > today:
            upcoming.append(exam)

        elif exam.exam_date == today:
            if current_time < exam.start_time:
                upcoming.append(exam)
            elif exam.start_time <= current_time <= exam.end_time:
                ongoing.append(exam)
            else:
                completed.append(exam)

        else:
            completed.append(exam)

    return render_template(
        "student_dashboard.html",
        upcoming=upcoming,
        ongoing=ongoing,
        completed=completed
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)