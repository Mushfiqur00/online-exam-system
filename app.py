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

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


@app.route("/admin-dashboard")
def admin_dashboard():

    if "role" not in session:
        return redirect("/")

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




@app.route("/create-group", methods=["GET","POST"])
def create_group():

    if request.method == "POST":

        name = request.form.get("name")

        if not name:
            flash("Group name required")
            return redirect("/group-management")

        existing = Group.query.filter_by(name=name).first()

        if existing:
            flash("Group already exists")
            return redirect("/group-management")

        group = Group(
            name=name,
            code=generate_code()
        )

        db.session.add(group)
        db.session.commit()

        flash("Group created successfully")

        return redirect("/group-management")

    groups = Group.query.all()

    return render_template(
        "group_management.html",
        groups=groups
    )


@app.route("/delete-group/<int:id>")
def delete_group(id):

    group = Group.query.get(id)

    db.session.delete(group)
    db.session.commit()

    return redirect("/group-management")


@app.route("/create-exam", methods=["POST"])
def create_exam():

    title = request.form.get("title")
    exam_date = request.form.get("exam_date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")
    duration = request.form.get("duration")

    if not title or not exam_date or not start_time or not end_time or not duration:
        flash("All fields required")
        return redirect("/create-exam-page")

    exam = Exam(
        title=title,
        exam_date=exam_date,
        start_time=start_time,
        end_time=end_time,
        duration=duration
    )

    db.session.add(exam)
    db.session.commit()

    flash("Exam created successfully")

    return redirect("/create-exam-page")


@app.route("/delete-exam/<int:id>")
def delete_exam(id):

    exam = Exam.query.get(id)

    if exam:
        db.session.delete(exam)
        db.session.commit()

    flash("Exam deleted")

    return redirect("/create-exam-page")

@app.route("/create-exam-page")
def create_exam_page():

    exams = Exam.query.all()

    return render_template(
        "create_exam.html",
        exams=exams
    )
@app.route("/assign-exam", methods=["POST"])
def assign_exam():

    exam_id = request.form.get("exam_id")
    student_id = request.form.get("student_id")
    group_id = request.form.get("group_id")

    if not exam_id:
        flash("Please select exam")
        return redirect("/admin-dashboard")

    # student assign
    if student_id:

        existing = ExamAssignment.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).first()

        if existing:
            flash("Already assigned to this student")
            return redirect("/admin-dashboard")

        assign = ExamAssignment(
            exam_id=exam_id,
            student_id=student_id
        )

        db.session.add(assign)


    # group assign
    elif group_id:

        existing = ExamAssignment.query.filter_by(
            exam_id=exam_id,
            group_id=group_id
        ).first()

        if existing:
            flash("Already assigned to this group")
            return redirect("/admin-dashboard")

        assign = ExamAssignment(
            exam_id=exam_id,
            group_id=group_id
        )

        db.session.add(assign)

    else:
        flash("Please select student or group")
        return redirect("/admin-dashboard")

    db.session.commit()

    flash("Exam assigned successfully")

    return redirect("/admin-dashboard")
    
@app.route("/clear-assignment/<int:exam_id>")
def clear_assignment(exam_id):

    assignments = ExamAssignment.query.filter_by(exam_id=exam_id).all()

    for a in assignments:
        db.session.delete(a)

    db.session.commit()

    flash("Assignments cleared")

    return redirect("/admin-dashboard")
   

if __name__ == "__main__":
    app.run(debug=True)