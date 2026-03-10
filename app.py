from flask import Flask, render_template, request, redirect, session, flash
from datetime import datetime
from models import db, Student, Exam, ExamAssignment, Group

app = Flask(__name__)
app.secret_key = "secretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():

    db.create_all()

    # Default group create
    if Group.query.count() == 0:

        g1 = Group(name="Group-1")
        g2 = Group(name="Group-2")

        db.session.add_all([g1, g2])
        db.session.commit()

    # Default students
    if Student.query.count() == 0:

        g1 = Group.query.filter_by(name="Group-1").first()
        g2 = Group.query.filter_by(name="Group-2").first()

        s1 = Student(username="Mushfiq", group_id=g1.id)
        s2 = Student(username="Subroto", group_id=g1.id)
        s3 = Student(username="Rakibul", group_id=g2.id)

        db.session.add_all([s1, s2, s3])
        db.session.commit()


# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "teacher" and password == "1234":
            session["role"] = "admin"
            return redirect("/admin-dashboard")

        elif username in ["Subroto", "Rakibul", "Mushfiq"]:
            session["role"] = "student"
            session["student_name"] = username
            return redirect("/student-dashboard")

        else:
            return "Invalid Credentials"

    return render_template("login.html")


# ADMIN DASHBOARD
@app.route("/admin-dashboard")
def admin_dashboard():

    if session.get("role") != "admin":
        return redirect("/")

    exams = Exam.query.all()
    students = Student.query.all()
    groups = Group.query.all()

    return render_template(
        "admin_dashboard.html",
        exams=exams,
        students=students,
        groups=groups
    )


# CREATE GROUP
@app.route("/create-group", methods=["POST"])
def create_group():

    group_name = request.form.get("group_name")

    new_group = Group(name=group_name)

    db.session.add(new_group)
    db.session.commit()

    flash("Group created successfully!")

    return redirect("/admin-dashboard")


# CREATE EXAM
@app.route("/create-exam", methods=["POST"])
def create_exam():

    title = request.form.get("title")
    exam_date = request.form.get("exam_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    duration = request.form.get("duration")

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


# ASSIGN EXAM
@app.route("/assign-exam", methods=["POST"])
def assign_exam():

    exam_id = request.form.get("exam_id")
    student_id = request.form.get("student_id")
    group_id = request.form.get("group_id")

    if student_id:

        assign = ExamAssignment(
            exam_id=exam_id,
            student_id=student_id
        )

        db.session.add(assign)

    if group_id:

        students = Student.query.filter_by(group_id=group_id).all()

        for student in students:

            assign = ExamAssignment(
                exam_id=exam_id,
                student_id=student.id
            )

            db.session.add(assign)

    db.session.commit()

    flash("Exam assigned successfully!")

    return redirect("/admin-dashboard")


# DELETE EXAM
@app.route("/delete-exam/<int:exam_id>")
def delete_exam(exam_id):

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

    exams = Exam.query.all()

    return render_template("student_dashboard.html", exams=exams)


# START EXAM
@app.route("/start-exam/<int:exam_id>")
def start_exam(exam_id):

    student = Student.query.filter_by(
        username=session["student_name"]
    ).first()

    assignment = ExamAssignment.query.filter_by(
        exam_id=exam_id,
        student_id=student.id
    ).first()

    if assignment is None:
        return "Not Assigned To You"

    exam = Exam.query.get(exam_id)

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    if today < exam.exam_date:
        return "Exam has not started yet"

    if today > exam.exam_date:
        return "Exam date is over"

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


if __name__ == "__main__":
    app.run(debug=True)