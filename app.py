from flask import Flask, render_template, request, redirect, session
from datetime import datetime
from models import db, Exam   # using Flask SQLAlchemy models

app = Flask(__name__)
app.secret_key = "secretkey"

# DATABASE CONFIG
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# LOGIN
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


# ADMIN DASHBOARD
@app.route("/admin-dashboard")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect("/")

    # changed from raw SQL to SQLAlchemy
    exams = Exam.query.order_by(Exam.exam_date, Exam.start_time).all()

    return render_template("admin_dashboard.html", exams=exams)


# CREATE EXAM
@app.route("/create-exam", methods=["POST"])
def create_exam():

    if session.get("role") != "admin":
        return redirect("/")

    title = request.form.get("title")
    exam_date = request.form.get("exam_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    duration = request.form.get("duration")

    # SQLAlchemy insert
    new_exam = Exam(
        title=title,
        exam_date=exam_date,
        start_time=start_time,
        end_time=end_time,
        duration=duration
    )

    db.session.add(new_exam)
    db.session.commit()

    return redirect("/admin-dashboard")


# DELETE EXAM
@app.route("/delete-exam/<int:exam_id>")
def delete_exam(exam_id):

    if session.get("role") != "admin":
        return redirect("/")

    exam = Exam.query.get(exam_id)

    if exam:
        db.session.delete(exam)
        db.session.commit()

    return redirect("/admin-dashboard")


# STUDENT DASHBOARD
@app.route("/student-dashboard")
def student_dashboard():

    if session.get("role") != "student":
        return redirect("/")

    exams = Exam.query.order_by(Exam.exam_date, Exam.start_time).all()

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    return render_template(
        "student_dashboard.html",
        exams=exams,
        today=today,
        current_time=current_time
    )


# START EXAM
@app.route("/start-exam/<int:exam_id>")
def start_exam(exam_id):

    if session.get("role") != "student":
        return redirect("/")

    exam = Exam.query.get(exam_id)

    if exam is None:
        return "Exam not found"

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    # Date check
    if today < exam.exam_date:
        return "Exam has not started yet"

    if today > exam.exam_date:
        return "Exam date is over"

    # Time check
    if current_time < exam.start_time:
        return "Exam has not started yet"

    if current_time > exam.end_time:
        return "Exam time is over"

    return "Exam Started Successfully"


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# RUN APP
if __name__ == "__main__":
    app.run(debug=True)