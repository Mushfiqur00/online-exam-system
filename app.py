from flask import Flask, render_template, request, redirect, flash, session , make_response
from models import db, Group, Student, Exam, ExamAssignment , Question , Result
from models import Student, Admin
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import string

from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"

import os # এটি ফাইলের একদম উপরে ইমপোর্ট করে নিন

# ডাটাবেস ইউআরআই সেটআপ
uri = os.environ.get('DATABASE_URL', 'sqlite:///database.db')

# Render-এ ডাটাবেস ইউআরএল 'postgres://' দিয়ে শুরু হয়, 
# but SQLAlchemy-uses 'postgresql://' is needed , thats why updated this  part
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

import os


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///examora.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def generate_code():

    letters = string.ascii_uppercase
    numbers = string.digits

    return ''.join(random.choice(letters+numbers) for i in range(6))



@app.route("/")
def home():
    return render_template("index.html")

@app.route("/support")
def support():
    return render_template("support.html")

from werkzeug.security import check_password_hash # ফাইলের উপরে ইমপোর্ট করো

from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role') # Hidden input থেকে role নিচ্ছি

        if role == 'student':
            student = Student.query.filter_by(username=username).first()
            # স্টুডেন্টের পাসওয়ার্ড রেজিস্ট্রেশনের সময় অটো হ্যাস হয়
            if student and check_password_hash(student.password, password):
                session['student_id'] = student.id
                flash("Login successful as Student!")
                return redirect(url_for('student_dashboard'))
            else:
                flash("Invalid Student credentials!")
                return redirect(url_for('login'))
                
        elif role == 'admin':
            admin = Admin.query.filter_by(username=username).first()
            # আমরা এখন অ্যাডমিনকেও হ্যাস পাসওয়ার্ড দিয়ে তৈরি করবো
            if admin and check_password_hash(admin.password, password):
                session['admin_id'] = admin.id 
                flash("Login successful as Admin!")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid Admin credentials!")
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'] # ফর্ম থেকে আসা পাসওয়ার্ড
        
        # ডাটাবেস থেকে অ্যাডমিনকে খোঁজা
        admin = Admin.query.filter_by(username=username).first()
        
        # --- এই লাইনটাই হলো আসল ম্যাজিক ---
        if admin and check_password_hash(admin.password, password):
            session['admin'] = admin.username
            flash("Admin logged in successfully!", "success")
            return redirect('/admin-dashboard') # আপনার ড্যাশবোর্ডের লিংকে রিডাইরেক্ট করুন
        else:
            flash("Invalid Admin credentials!", "danger")
            return redirect('/admin-login')
            
    return render_template('admin_login.html')

@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin" not in session:
        redirect("/login")

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

@app.route("/student-register", methods=["GET","POST"])
def student_register():
    if request.method == "POST":
        # .get() ব্যবহার করলে ডাটা না থাকলেও সার্ভার ক্র্যাশ করবে না
        name = request.form.get("name")
        student_id = request.form.get("student_id")
        email = request.form.get("email")
        phone = request.form.get("phone")
        username = request.form.get("username")
        password = request.form.get("password")
        group_code = request.form.get("group_code")

        group = Group.query.filter_by(code=group_code).first()
        if not group:
            flash("Invalid Group Code! Please contact your teacher.")
            return redirect("/student-register")

        # পাসওয়ার্ড হ্যাস করে সেভ করুন
        hashed_pw = generate_password_hash(password)

        student = Student(
            name=name,
            student_id=student_id,
            email=email,
            phone=phone,
            username=username,
            password=hashed_pw,
            group_id=group.id
        )

        # সার্ভার ক্র্যাশ রোধ করার জন্য try-except ব্লক
        try:
            db.session.add(student)
            db.session.commit()
            flash("Registration Successful! Please Login.")
            return redirect("/login")
        except Exception as e:
            db.session.rollback() # ডাটাবেস আটকে গেলে ছাড়িয়ে দিবে
            flash("Registration Failed! Username or Student ID already exists.")
            return redirect("/student-register")

    return render_template("register.html")

@app.route("/student-dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect("/login")

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
# ✅ mushfiq
@app.route("/start-exam/<int:exam_id>", methods=["GET", "POST"])
def start_exam(exam_id):
    if "student_id" not in session:
        return redirect("/login")
    
    exam = Exam.query.get_or_404(exam_id)
    student = Student.query.get(session["student_id"])
    
    # প্রশ্নগুলো আনা
    questions = Question.query.filter_by(exam_id=exam.id).all()

    # পরীক্ষা সাবমিট করা থাকলে আবার শুরু করতে দেওয়া হবে না
    existing = Result.query.filter_by(student_id=student.id, exam_id=exam.id).first()
    if existing:
        flash("You have already submitted this exam!")
        return redirect("/student-dashboard")

    # যখন স্টুডেন্ট ফর্ম সাবমিট করবে (পরীক্ষা শেষ করবে)
    if request.method == "POST":
        obtained_marks = 0
        has_short = False
        
        for q in questions:
            # HTML ফর্মে name="q_{{q.id}}" থাকতে হবে
            user_ans = request.form.get(f"q_{q.id}")
            
            is_correct = False
            marks_for_this_q = 0
            
            # MCQ এর ক্ষেত্রে সঠিক উত্তর চেক করা
            if q.question_type == "mcq":
                if user_ans and user_ans.strip().lower() == q.correct_answer.strip().lower():
                    obtained_marks += int(q.marks)
                    marks_for_this_q = int(q.marks)
                    is_correct = True
            else:
                has_short = True

            # 🔥 ১. StudentAnswer টেবিলে প্রতিটি প্রশ্নের উত্তর সেভ করা হচ্ছে
            student_answer = StudentAnswer(
                student_id=student.id,
                exam_id=exam.id,
                question_id=q.id,
                user_answer=user_ans,
                marks_obtained=marks_for_this_q,
                is_correct=is_correct
            )
            db.session.add(student_answer)

        final_status = "Pending" if has_short else "Evaluated"

        # 🔥 ২. Result টেবিলে টোটাল স্কোর সেভ করা হচ্ছে
        new_result = Result(
            student_id=student.id, 
            exam_id=exam.id, 
            score=obtained_marks,
            status=final_status
        )
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
        return redirect("/login")
    
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
# ১. এখানে methods=["GET", "POST"] যোগ করা হয়েছে যাতে বাটন ক্লিক করলে এরর না আসে।
@app.route("/toggle-publish/<int:exam_id>", methods=["GET", "POST"])
def toggle_publish(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    
    # এক্সামের পাবলিশ স্ট্যাটাস উল্টে দেওয়া (True থাকলে False, False থাকলে True)
    exam.is_published = not exam.is_published
    
    db.session.commit()
    
    # কাজ শেষে আবার আগের পেজেই ফেরত পাঠাবে
    return redirect(request.referrer or "/admin-dashboard")

@app.route("/submit-exam/<int:exam_id>", methods=["POST"])
def submit_exam(exam_id):
    if "student_id" not in session:
        return redirect("/login")

    student_id = session["student_id"]

    # 🔒 ডাবল সাবমিট রোধ (কেউ যেন দুইবার পরীক্ষা দিতে না পারে)
    existing = Result.query.filter_by(
        student_id=student_id,
        exam_id=exam_id
    ).first()

    if existing:
        flash("You have already submitted this exam!")
        return redirect("/student-dashboard")

    questions = Question.query.filter_by(exam_id=exam_id).all()
    exam = Exam.query.get(exam_id) 

    total_marks = 0
    obtained_marks = 0
    has_short = False

    for q in questions:
        user_ans = request.form.get(f"q{q.id}")
        total_marks += int(q.marks)

        is_correct = False
        marks_for_this_q = 0

        if q.question_type == "mcq":
            # user_ans খালি আছে কিনা তা চেক করে নেওয়া ভালো
            if user_ans and user_ans == q.correct_answer:
                obtained_marks += int(q.marks)
                marks_for_this_q = int(q.marks)
                is_correct = True
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

   
    flash("Exam submitted successfully! To see your result, please go to the 'My Results' section.")
    return redirect("/student-dashboard")

# --- Mushfiqur's Code: Feature 2 (Student Results View) ---
@app.route("/my-results")
def my_results():
    if "student_id" not in session: return redirect("/login")
    student_id = session["student_id"]
    
    # 🟢 ডাটাবেস থেকে বর্তমান স্টুডেন্টের ডাটা বের করা
    student = Student.query.get(student_id) 
    
    # 🛡️ এক্সট্রা সেফটি চেক: ডাটাবেসে স্টুডেন্ট না থাকলে সেশন ক্লিয়ার করে বের করে দেবে
    if not student:
        session.clear()
        return redirect("/")
    
    results = Result.query.filter_by(student_id=student_id).all()
    
    exams_data = []
    
    # Chart-এর জন্য লিস্ট তৈরি
    chart_labels = []
    chart_scores = []
    
    # স্ট্যাটাস কাউন্ট করার জন্য
    evaluated_count = 0
    pending_count = 0

    for r in results:
        exam = Exam.query.get(r.exam_id)
        exams_data.append({"result": r, "exam": exam})
        
        # Bar Chart এর ডাটা
        chart_labels.append(exam.title)
        if exam.is_published and r.score is not None:
            chart_scores.append(r.score)
        else:
            chart_scores.append(0) 
            
        # Pie Chart এর ডাটা
        if r.status == "Evaluated":
            evaluated_count += 1
        else:
            pending_count += 1

    return render_template("my_results.html", 
                           student=student,  # 🟢 স্টুডেন্টের ডাটা HTML এ পাস করা হলো
                           exams_data=exams_data,
                           chart_labels=chart_labels,
                           chart_scores=chart_scores,
                           evaluated_count=evaluated_count,
                           pending_count=pending_count)

@app.route("/result-details/<int:exam_id>")
def result_details(exam_id):
    if "student_id" not in session: 
        return redirect("/login")
        
    student_id = session["student_id"]
    student = Student.query.get(student_id) # লেআউটের জন্য স্টুডেন্ট ডাটা
    
    result = Result.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    exam = Exam.query.get_or_404(exam_id)
    
    if not result:
        flash("Result not found!")
        return redirect("/student-dashboard")
        
    answers = db.session.query(StudentAnswer, Question).join(
        Question, StudentAnswer.question_id == Question.id
    ).filter(
        StudentAnswer.student_id == student_id, 
        StudentAnswer.exam_id == exam_id
    ).all()
    
    total_questions = len(answers)
    correct_count = sum(1 for ans, q in answers if ans.is_correct)
    wrong_count = total_questions - correct_count
    
    return render_template("result_details.html", 
                           answers=answers, 
                           result=result, 
                           exam=exam,
                           student=student,
                           total_questions=total_questions,
                           correct_count=correct_count,
                           wrong_count=wrong_count)

# --- Student Profile ---
@app.route("/profile")
def profile():
    if "student_id" not in session:
        return redirect("/login")
    
    student = Student.query.get(session["student_id"])
    # স্টুডেন্ট কয়টা পরীক্ষা দিয়েছে তার একটা হিসাব (অপশনাল কিন্তু দেখতে ভালো লাগে)
    total_exams = Result.query.filter_by(student_id=student.id).count()
    
    return render_template("profile.html", student=student, total_exams=total_exams)

#Feature 3 (Admin View Stats & Submissions) ---
@app.route("/admin/exam-results/<int:exam_id>")
def admin_exam_results(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    results = Result.query.filter_by(exam_id=exam_id).all()
    
    total_students = len(results)
    avg_score = sum([r.score for r in results]) / total_students if total_students > 0 else 0
    
    student_data = []
    for r in results:
        student = Student.query.get(r.student_id)
        student_data.append({"result": r, "student": student})
        
    return render_template("admin_exam_results.html", exam=exam, stats={"total": total_students, "avg": round(avg_score, 2)}, student_data=student_data)

@app.route("/admin/student-submission/<int:result_id>")
def admin_student_submission(result_id):
    result = Result.query.get_or_404(result_id)
    
    # Sora-sori result table-er foreign keys use korun match korar jonno
    student = Student.query.get(result.student_id)
    exam = Exam.query.get(result.exam_id)
    
    # Filter korar somoy result table-e thaka exact foreign keys pathan
    answers = StudentAnswer.query.filter_by(
        student_id=result.student_id, 
        exam_id=result.exam_id
    ).all()
    
    # terminal-e check korun koto dekhay (eta fix korte khub help korbe)
    print(f"--- DEBUG INFO ---")
    print(f"Exam ID: {result.exam_id}, Student ID: {result.student_id}")
    print(f"Answers Found: {len(answers)}")
    
    return render_template("admin_student_submission.html", 
                           result=result, student=student, 
                           exam=exam, answers=answers)



#for short question 

from flask import request, flash, redirect

@app.route("/admin/evaluate-submission/<int:result_id>", methods=["POST"])
def evaluate_submission(result_id):
    if "admin" not in session: # সিকিউরিটির জন্য (যদি তোমার অ্যাডমিন সেশন অন্য নামে থাকে, তবে সেটা দিও)
        return redirect("/admin-login")

    result = Result.query.get_or_404(result_id)
    answers = StudentAnswer.query.filter_by(student_id=result.student_id, exam_id=result.exam_id).all()
    
    for ans in answers:
        if ans.question.question_type == "short":
            # ফর্ম থেকে মার্কস নেওয়া হচ্ছে
            mark_input = request.form.get(f"mark_{ans.id}")
            if mark_input is not None and mark_input.strip() != "":
                ans.marks_obtained = float(mark_input)
                # মার্কস 0 এর বেশি হলে সঠিক ধরা যেতে পারে, তবে শর্ট প্রশ্নের জন্য marks টাই আসল
                ans.is_correct = True if float(mark_input) > 0 else False

    # নতুন করে টোটাল স্কোর ক্যালকুলেট করা
    total_score = sum(ans.marks_obtained for ans in answers if ans.marks_obtained is not None)
    
    # রেজাল্ট আপডেট
    result.score = total_score
    result.status = "Evaluated"
    db.session.commit()
    
    flash("Evaluation saved successfully!", "success")
    return redirect(f"/admin/exam-results/{result.exam_id}")

# --- ডাটাবেস এবং অ্যাডমিন সেটআপ ---
with app.app_context():
 
    db.create_all() # এবার নতুন সাইজ (255) অনুযায়ী ফ্রেশ টেবিল বানাবে
    
    admin = Admin.query.filter_by(username='teacher').first()
    if not admin:
        from werkzeug.security import generate_password_hash
        new_admin = Admin(username='teacher', password=generate_password_hash('1234'))
        db.session.add(new_admin)
        db.session.commit()
        print("Admin created automatically!")

# --- লোকাল সার্ভার রান করার জন্য ---
if __name__ == '__main__':
    app.run(debug=True)