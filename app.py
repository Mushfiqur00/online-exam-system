from flask import Flask, render_template, request, redirect, flash, session , make_response
from models import db, Group, Student, Exam, ExamAssignment , Question , Result
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

    
    for exam in exams:
        exam.question_count = Question.query.filter_by(exam_id=exam.id).count()

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
    results = db.session.query(Result, Exam).join(Exam, Result.exam_id == Exam.id).filter(Result.student_id == student.id).all()
    exams = Exam.query.all()

    today = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")

    upcoming = []
    ongoing = []
    completed = []

    for exam in exams:
        # Check if the exam is assigned to this student or their group
        assignment = ExamAssignment.query.filter(
            (ExamAssignment.exam_id == exam.id) &
            (
                (ExamAssignment.student_id == student.id) |
                (ExamAssignment.group_id == student.group_id)
            )
        ).first()

        exam.assigned = assignment is not None

        # Check if the student has already submitted this exam
        existing_result = Result.query.filter_by(
            student_id=student.id,
            exam_id=exam.id
        ).first()

        exam.submitted = existing_result is not None

        # Logic for categorizing exams based on date and time
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
        current_time=current_time,
        results=results
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


# ✅ mushfiq
@app.route("/start-exam/<int:exam_id>", methods=["GET", "POST"])
def start_exam(exam_id):
    if "student_id" not in session:
        return redirect("/")
    
    exam = Exam.query.get_or_404(exam_id)
    student = Student.query.get(session["student_id"])
    
    # প্রশ্নগুলো আনা (models.py অনুযায়ী)
    questions = Question.query.filter_by(exam_id=exam.id).all()

    # যখন স্টুডেন্ট ফর্ম সাবমিট করবে (পরীক্ষা শেষ করবে)
    if request.method == "POST":
        total_score = 0
        
        for q in questions:
            # HTML ফর্মে name="q_{{q.id}}" থাকবে
            selected_option = request.form.get(f"q_{q.id}")
            
            # MCQ এর ক্ষেত্রে সঠিক উত্তর চেক করা
            if q.question_type == "mcq":
                if selected_option and selected_option.strip().lower() == q.correct_answer.strip().lower():
                    total_score += q.marks
        
        # রেজাল্ট ডাটাবেজে সেভ করা
        new_result = Result(student_id=student.id, exam_id=exam.id, score=total_score)
        db.session.add(new_result)
        db.session.commit()
        
        flash("Exam submitted successfully!")
        return redirect("/student-dashboard")

    return render_template("start_exam.html", exam=exam, questions=questions, student=student)


@app.route("/delete-exam/<int:id>")
def delete_exam(id):

    exam = Exam.query.get(id)

    if exam:
        db.session.delete(exam)
        db.session.commit()

    flash("Exam deleted")

    return redirect("/admin-dashboard")

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

        if not existing:
            assign = ExamAssignment(
                exam_id=exam_id,
                student_id=student_id
            )
            db.session.add(assign)

    # group assign
    if group_id:
        existing = ExamAssignment.query.filter_by(
            exam_id=exam_id,
            group_id=group_id
        ).first()

        if not existing:
            assign = ExamAssignment(
                exam_id=exam_id,
                group_id=group_id
            )
            db.session.add(assign)

    # nothing selected
    if not student_id and not group_id:
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




# ✅ shubroto
#add question
@app.route("/add-question/<int:exam_id>", methods=["GET","POST"])
def add_question(exam_id):

    # 🔹 existing question gula anar jonno
    questions = Question.query.filter_by(exam_id=exam_id).all()

    if request.method == "POST":

        question_text = request.form.get("question_text")
        question_type = request.form.get("question_type")
        
        # HTML ফর্মের name অনুযায়ী ডাটা নেওয়া (নিশ্চিত করুন HTML এ name="option_a" আছে)
        option_a = request.form.get("option_a") 
        option_b = request.form.get("option_b")
        option_c = request.form.get("option_c")
        option_d = request.form.get("option_d")
        
        correct_answer = request.form.get("correct_answer")
        marks = request.form.get("marks")

        # ✅ validation
        if not question_text or not question_type or not marks:
            flash("সব field fill korte hobe")
            return redirect(f"/add-question/{exam_id}")

        if question_type == "mcq":
            if not option_a or not option_b or not option_c or not option_d:
                flash("MCQ হলে সব option dite hobe")
                return redirect(f"/add-question/{exam_id}")

            if not correct_answer:
                flash("Correct answer dite hobe")
                return redirect(f"/add-question/{exam_id}")

        # ✅ save (এখানেই ভুল ছিল, কলামের নামগুলো মডেলে যা আছে তা দিতে হবে)
        question = Question(
            exam_id=exam_id,
            question_text=question_text,
            question_type=question_type,
            option_a=option_a,   # model.py এর সাথে মিল রেখে
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            marks=marks
        )

        db.session.add(question)
        db.session.commit()

        # 🔥 same page e thakbe (multiple add possible)
        return redirect(f"/add-question/{exam_id}")

    return render_template(
        "add_question.html",
        exam_id=exam_id,
        questions=questions
    )

# ✅ mushfiq

from models import StudentAnswer # ফাইলের উপরে যেখানে ইমপোর্টগুলো আছে সেখানে এটি যোগ করবেন


# =====================================================
# RAKIBUL FEATURE
# Admin delete question
# =====================================================


@app.route("/delete-question/<int:id>/<int:exam_id>", methods=["POST"])
def delete_question(id, exam_id):
    q = Question.query.get(id)
    if q:
        db.session.delete(q)
        db.session.commit()
        flash("Question deleted!")
    
    return redirect(f"/add-question/{exam_id}")

# =====================================================
# RAKIBUL FEATURE
# Admin edit question
# =====================================================

@app.route("/edit-question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    if request.method == "POST":
        question.question_text = request.form.get("question_text")
        question.question_type = request.form.get("question_type")
        question.option_a = request.form.get("option_a")
        question.option_b = request.form.get("option_b")
        question.option_c = request.form.get("option_c")
        question.option_d = request.form.get("option_d")
        question.correct_answer = request.form.get("correct_answer")
        question.marks = request.form.get("marks")
        
        db.session.commit()
        flash("Question updated successfully!")
        return redirect(f"/add-question/{question.exam_id}")

    return render_template("edit_question.html", q=question)




# ✅ mushfiq
@app.route("/exam-instruction/<int:exam_id>")
def exam_instruction(exam_id):
    if "student_id" not in session:
        return redirect("/")
    
    exam = Exam.query.get_or_404(exam_id)
    student = Student.query.get(session["student_id"])
    
    # পরীক্ষা সাবমিট করা থাকলে আবার শুরু করতে দেওয়া হবে না
    has_submitted = Result.query.filter_by(student_id=student.id, exam_id=exam.id).first()
    if has_submitted:
        flash("You have already submitted this exam!")
        return redirect("/student-dashboard")

    return render_template("exam_instruction.html", exam=exam, student=student)












# =====================================================
# FEATURE WORK - Corrected & Linked
# =====================================================

@app.route("/admin-results")
def admin_results_view(): # নাম পরিবর্তন করা হয়েছে ডুপ্লিকেট এড়াতে
    results = Result.query.all()
    return render_template("admin_results.html", results=results) 

@app.route("/profile")
def student_profile():
    if "student_id" not in session:
        return redirect("/")
    student = Student.query.get(session["student_id"])
    return render_template("profile.html", student=student)

@app.route("/question-bank")
def view_question_bank():
    # ডাটাবেজ থেকে সব প্রশ্ন নিয়ে টেম্পলেটে পাঠানো হচ্ছে
    all_questions = Question.query.all()
    return render_template("question_bank.html", questions=all_questions)

@app.route('/students')
def view_students():
    all_students = Student.query.all()
    all_groups = Group.query.all() # এটি অবশ্যই ডাটাবেজ থেকে আনতে হবে
    return render_template('students.html', students=all_students, groups=all_groups)


@app.route("/settings")
def admin_settings_page():
    # নিশ্চিত করুন আপনার ফাইলে অন্য কোথাও 'def settings():' নেই
    return render_template("settings.html")

@app.route('/update-student-group/<int:id>', methods=['POST'])
def update_student_group(id):
    student = Student.query.get_or_404(id)
    new_group_id = request.form.get('group_id')
    
    # ড্রপডাউনে কিছু না থাকলে (Select Group) গ্রুপ রিমুভ হবে
    student.group_id = new_group_id if new_group_id else None
    
    db.session.commit()
    return redirect('/students')

# --- Rakibul's Code: Feature 4 (Publish/Hide) ---
@app.route("/toggle-publish/<int:exam_id>")
def toggle_publish(exam_id):
    results = Result.query.filter_by(exam_id=exam_id).all()
    if results:
        # Toggle current state based on the first result's state
        new_state = not results[0].is_published 
        for r in results: r.is_published = new_state
        db.session.commit()
    return redirect("/create-exam") # Redirect back to admin exam list




@app.route("/submit-exam/<int:exam_id>", methods=["POST"])
def submit_exam(exam_id):
    if "student_id" not in session:
        return redirect("/")

    student_id = session["student_id"]

    # 🔒 prevent double submit
    existing = Result.query.filter_by(
        student_id=student_id,
        exam_id=exam_id
    ).first()

    if existing:
        return redirect("/student-dashboard")

    questions = Question.query.filter_by(exam_id=exam_id).all()

    total_marks = 0
    obtained_marks = 0
    correct_count = 0
    wrong_count = 0
    has_short = False

    for q in questions:
        user_ans = request.form.get(f"q{q.id}")
        total_marks += int(q.marks)

        is_correct = False
        marks_for_this_q = 0

        if q.question_type == "mcq":
            if user_ans == q.correct_answer:
                obtained_marks += int(q.marks)
                marks_for_this_q = int(q.marks)
                correct_count += 1
                is_correct = True
            else:
                wrong_count += 1
        else:
            has_short = True
        
        student_answer = StudentAnswer(
            student_id=student_id,
            exam_id=exam_id,
            question_id=q.id,
            user_answer=user_ans,
            marks_obtained=marks_for_this_q,
            is_correct=is_correct
        )
        db.session.add(student_answer)

    final_status = "Pending" if has_short else "Evaluated"

    result = Result(
        student_id=student_id,
        exam_id=exam_id,
        score=obtained_marks,
        status=final_status
    )
    db.session.add(result)
    db.session.commit()

    return render_template(
        "result.html",
        total=total_marks,
        obtained=obtained_marks,
        correct=correct_count,
        wrong=wrong_count,
        has_short=has_short,
        status=final_status
    )

if __name__ == "__main__":


    app.run(debug=True)

