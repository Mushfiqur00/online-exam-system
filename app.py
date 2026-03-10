from flask import Flask, render_template, request, redirect, flash, session
from models import db, Group, Student, Exam, ExamAssignment
import random
import string

app = Flask(__name__)
app.secret_key = "secret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def generate_code():

    letters = string.ascii_uppercase
    numbers = string.digits

    return ''.join(random.choice(letters+numbers) for i in range(6))


@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == "teacher" and password == "1234":

            session["role"] = "admin"

            return redirect("/admin-dashboard")

    return render_template("login.html")


@app.route("/admin-dashboard")
def admin_dashboard():

    exams = Exam.query.all()
    students = Student.query.all()
    groups = Group.query.all()
    assignments = ExamAssignment.query.all()

    return render_template(
        "admin_dashboard.html",
        exams=exams,
        students=students,
        groups=groups,
        assignments=assignments
    )


@app.route("/group-management")
def group_management():

    groups = Group.query.all()

    return render_template(
        "group_management.html",
        groups=groups
    )

@app.route("/delete-exam/<int:id>")
def delete_exam(id):

    exam = Exam.query.get(id)

    if exam:
        db.session.delete(exam)
        db.session.commit()

    flash("Exam deleted")

    return redirect("/admin-dashboard")


@app.route("/create-group", methods=["GET","POST"])
def create_group():

    if request.method == "POST":

        name = request.form.get("name")

        if not name:
            flash("Group name required")
            return redirect("/create-group")

        # duplicate check
        existing = Group.query.filter_by(name=name).first()

        if existing:
            flash("Group already exists")
            return redirect("/create-group")

        group = Group(
            name=name,
            code=generate_code()
        )

        db.session.add(group)
        db.session.commit()

        flash("Group created successfully")

        return redirect("/create-group")

    return render_template("group_management.html")

@app.route("/create-exam-page")
def create_exam_page():

    exams = Exam.query.all()

    return render_template(
        "create_exam.html",
        exams=exams
    )


@app.route("/create-exam", methods=["POST"])
def create_exam():

    title = request.form.get("title")
    exam_date = request.form.get("exam_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    duration = request.form.get("duration")

    # validation
    if not title or not exam_date or not start_time or not end_time or not duration:
        flash("All fields are required!")
        return redirect("/create-exam")

    exam = Exam(
        title=title,
        exam_date=exam_date,
        start_time=start_time,
        end_time=end_time,
        duration=duration
    )

    db.session.add(exam)
    db.session.commit()

    flash("Exam created successfully!")

    return redirect("/admin-dashboard")

@app.route("/assign-exam", methods=["POST"])
def assign_exam():

    exam_id = request.form.get("exam_id")
    student_id = request.form.get("student_id")
    group_id = request.form.get("group_id")

    # exam select check
    if not exam_id:
        flash("Please select an exam")
        return redirect("/admin-dashboard")

    # group or student select check
    if not student_id and not group_id:
        flash("Please select a student or a group")
        return redirect("/admin-dashboard")

    # assign to individual student
    if student_id:

        assign = ExamAssignment(
            exam_id=exam_id,
            student_id=student_id
        )

        db.session.add(assign)

    # assign to group
    if group_id:

        students = Student.query.filter_by(group_id=group_id).all()

        if not students:
            flash("No students found in this group")
            return redirect("/admin-dashboard")

        for s in students:

            assign = ExamAssignment(
                exam_id=exam_id,
                student_id=s.id
            )

            db.session.add(assign)

    db.session.commit()

    flash("Exam assigned successfully")

    return redirect("/admin-dashboard")


if __name__ == "__main__":
    app.run(debug=True)