<<<<<<< HEAD
# Main code part
=======
from flask import Flask, render_template, request, redirect, session, flash
from datetime import datetime
from models import db, Student, Exam, ExamAssignment

app = Flask(__name__)
app.secret_key = "secretkey"

# DATABASE CONFIG
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():

    db.create_all()

    if Student.query.count() == 0:
        s1 = Student(username="Mushfiq")
        s2 = Student(username="Subroto")
        s3 = Student(username="Rakibul")

        db.session.add_all([s1, s2, s3])
        db.session.commit()
             # LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Admin login
        if username == "teacher" and password == "1234":
            session["role"] = "admin"
            return redirect("/admin-dashboard")

        # Student logins
        elif username == "Subroto" and password == "1036":
            session["role"] = "student"
            return redirect("/student-dashboard")

        elif username == "Rakibul" and password == "1273":
            session["role"] = "student"
            return redirect("/student-dashboard")

        elif username == "Mushfiq" and password == "1405":
            session["role"] = "student"
            return redirect("/student-dashboard")

        else:
            return "Invalid Credentials"

    return render_template("login.html")

# ADMIN DASHBOARD
@app.route("/admin-dashboard")
def admin_dashboard():

    # Your security check
    if session.get("role") != "admin":
        return redirect("/")

    # Your exam ordering improvement
    exams = Exam.query.order_by(Exam.exam_date, Exam.start_time).all()

    # Shubroto's student list (needed for assignment)
    students = Student.query.all()

    return render_template(
        "admin_dashboard.html",
        exams=exams,
        students=students
    )

# ASSIGN EXAM (Individual or Group)

@app.route("/assign-exam", methods=["POST"])
def assign_exam():
    exam_id = request.form.get("exam_id")
    student_id = request.form.get("student_id")
    group_name = request.form.get("group_name")

    # Assign to individual student
    if student_id:
        new_assignment = ExamAssignment(
            exam_id=exam_id,
            student_id=student_id
        )
        db.session.add(new_assignment)

    # Assign to group of students
    if group_name:
        group_students = Student.query.filter_by(
            group_name=group_name
        ).all()

        for student in group_students:
            new_assignment = ExamAssignment(
                exam_id=exam_id,
                student_id=student.id
            )
            db.session.add(new_assignment)

    db.session.commit()
    flash("Exam assigned successfully!")
    return redirect("/admin-dashboard")



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

    upcoming = []
    ongoing = []
    completed = []

    for exam in exams:

        if exam.exam_date > today:
            upcoming.append(exam)

        elif exam.exam_date == today:

            if exam.start_time <= current_time <= exam.end_time:
                ongoing.append(exam)
            else:
                upcoming.append(exam)

        else:
            completed.append(exam)

    return render_template(
        "student_dashboard.html",
        upcoming=upcoming,
        ongoing=ongoing,
        completed=completed,
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
>>>>>>> module1
