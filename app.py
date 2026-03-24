from flask import Flask, render_template, request, redirect, flash, session , make_response
from models import db, Group, Student, Exam, ExamAssignment , Question
import random
import string

from datetime import datetime

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

@app.route("/student-register", methods=["GET","POST"])
def student_register():

    if request.method == "POST":

        name = request.form["name"]
        student_id = request.form["student_id"]
        email = request.form["email"]
        phone = request.form["phone"]
        username = request.form["username"]
        password = request.form["password"]
        group_code = request.form["group_code"]

        group = Group.query.filter_by(code=group_code).first()

        if not group:
            return "Invalid Group Code"

        student = Student(
            name=name,
            student_id=student_id,
            email=email,
            phone=phone,
            username=username,
            password=password,
            group_id=group.id
        )

        db.session.add(student)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")


@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "teacher" and password == "1234":
            session["admin"] = True
            return redirect("/admin-dashboard")

        student = Student.query.filter_by(
            username=username,
            password=password
        ).first()

        if student:
            session["student_id"] = student.id
            return redirect("/student-dashboard")

        return "Invalid Login"

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")




@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/")

    exams = Exam.query.all()
    students = Student.query.all()
    groups = Group.query.all()
    assignments = ExamAssignment.query.all()

    response = make_response(render_template(
        "admin_dashboard.html",
        exams=exams,
        students=students,
        groups=groups,
        assignments=assignments
    ))

    response.headers["Cache-Control"] = "no-store"

    return response

@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect("/")

    student = Student.query.get(session["student_id"])

    exams = Exam.query.all()

    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")

    upcoming = []
    ongoing = []
    completed = []

    for exam in exams:

        assignment = ExamAssignment.query.filter(
            (ExamAssignment.exam_id == exam.id) &
            (
                (ExamAssignment.student_id == student.id) |
                (ExamAssignment.group_id == student.group_id)
            )
        ).first()

        exam.assigned = assignment is not None

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

        student=student,
        upcoming=upcoming,
        ongoing=ongoing,
        completed=completed,
        today=today,
        current_time=current_time
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
   
@app.route("/start-exam/<int:exam_id>")
def start_exam(exam_id):

    if "student_id" not in session:
        return redirect("/")

    exam = Exam.query.get(exam_id)

    questions = Question.query.filter_by(exam_id=exam_id).all()

    return render_template(
        "exam_page.html",
        questions=questions,
        exam_id=exam_id,
        duration=exam.duration
    )


@app.route("/add-question/<int:exam_id>", methods=["GET","POST"])
def add_question(exam_id):

    if request.method == "POST":

        question_text = request.form.get("question_text")
        question_type = request.form.get("question_type")

        option1 = request.form.get("option1")
        option2 = request.form.get("option2")
        option3 = request.form.get("option3")
        option4 = request.form.get("option4")

        correct_answer = request.form.get("correct_answer")

        marks = request.form.get("marks")

        question = Question(
            exam_id=exam_id,
            question_text=question_text,
            question_type=question_type,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_answer=correct_answer,
            marks=marks
        )

        db.session.add(question)
        db.session.commit()

        return redirect("/create-exam-page")

    return render_template("add_question.html", exam_id=exam_id)


#rafi add your code here 
# =====================================================
# RAKIBUL FEATURE
# Admin delete question
# =====================================================

@app.route("/delete-question/<int:id>")
def delete_question(id):

    q = Question.query.get(id)

    db.session.delete(q)
    db.session.commit()

    return redirect("/create-exam-page")


# =====================================================
# RAKIBUL FEATURE
# Admin edit question
# =====================================================

@app.route("/edit-question/<int:id>", methods=["GET","POST"])
def edit_question(id):

    q = Question.query.get(id)

    if request.method == "POST":

        q.question_text = request.form.get("question_text")
        q.correct_answer = request.form.get("correct_answer")
        q.marks = request.form.get("marks")

        db.session.commit()

        return redirect("/create-exam-page")

    return render_template("edit_question.html", q=q)






























if __name__ == "__main__":


    app.run(debug=True)