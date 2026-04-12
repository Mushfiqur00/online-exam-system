import os
import random
import string
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash

# নিশ্চিত করুন models.py এ এই সব ক্লাস/ফাংশন ঠিকমতো লেখা আছে
from models import db, Group, Student, Admin, Exam, ExamAssignment, Question, Result, StudentAnswer, ActivityLog, log_activity

app = Flask(__name__)
app.secret_key = "secret"

# ডাটাবেস ইউআরআই সেটআপ
uri = os.environ.get('DATABASE_URL', 'sqlite:///examora.db')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role') 

        if role == 'student':
            student = Student.query.filter_by(username=username).first()
            if student and check_password_hash(student.password, password):
                session['student_id'] = student.id
                session['role'] = 'student'
                flash("Login successful as Student!")
                return redirect(url_for('student_dashboard'))
            else:
                flash("Invalid Student credentials!")
                return redirect(url_for('login'))
                
        elif role == 'admin':
            admin = Admin.query.filter_by(username=username).first()
            if admin and check_password_hash(admin.password, password):
                session['admin_id'] = admin.id 
                session['role'] = 'admin'
                flash("Login successful as Admin!")
                log_activity(f"Admin '{username}' logged in") #📜
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid Admin credentials!")
                return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            session['role'] = 'admin'
            flash("Admin logged in successfully!", "success")
            return redirect('/admin-dashboard')
        else:
            flash("Invalid Admin credentials!", "danger")
            return redirect('/admin-login')
            
    return render_template('admin_login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/admin-dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        return redirect("/login")

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
        name = request.form.get("name")
        student_id = request.form.get("student_id")
        email = request.form.get("email")
        phone = request.form.get("phone")
        username = request.form.get("username")
        password = request.form.get("password")
        group_code = request.form.get("group_code")

        group = Group.query.filter_by(code=group_code).first()
        if not group:
            flash("Invalid Group Code! Please contact your teacher.", "danger")
            return redirect("/student-register")

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

        try:
            db.session.add(student)
            db.session.commit()
            flash("Registration Successful! Please Login.", "success")
            return redirect("/login")
        except Exception as e:
            db.session.rollback()
            flash("Registration Failed! Username or Student ID already exists.", "danger")
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
        assignment = ExamAssignment.query.filter(
            (ExamAssignment.exam_id == exam.id) &
            (
                (ExamAssignment.student_id == student.id) |
                (ExamAssignment.group_id == student.group_id)
            )
        ).first()

        exam.assigned = assignment is not None

        existing_result = Result.query.filter_by(
            student_id=student.id,
            exam_id=exam.id
        ).first()

        exam.submitted = existing_result is not None

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
    return render_template("group_management.html", groups=groups)

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

        group = Group(name=name, code=generate_code())
        db.session.add(group)
        db.session.commit()
        
        log_activity(f"Created a new group: {name}") #📜
        flash("Group created successfully")
        return redirect("/group-management")

    groups = Group.query.all()
    return render_template("group_management.html", groups=groups)

@app.route("/delete-group/<int:id>")
def delete_group(id):
    group = Group.query.get(id)
    if group:
        db.session.delete(group)
        db.session.commit()
        log_activity(f"Deleted group: {group.name}") #📜
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

    log_activity(f"Created a new exam: {title}") #📜
    flash("Exam created successfully")
    return redirect("/create-exam-page")

@app.route("/start-exam/<int:exam_id>", methods=["GET", "POST"])
def start_exam(exam_id):
    if "student_id" not in session:
        return redirect("/login")
    
    exam = Exam.query.get_or_404(exam_id)
    student = Student.query.get(session["student_id"])
    questions = Question.query.filter_by(exam_id=exam.id).all()

    existing = Result.query.filter_by(student_id=student.id, exam_id=exam.id).first()
    if existing:
        flash("You have already submitted this exam!")
        return redirect("/student-dashboard")

    if request.method == "POST":
        obtained_marks = 0
        has_short = False
        
        for q in questions:
            user_ans = request.form.get(f"q_{q.id}")
            is_correct = False
            marks_for_this_q = 0
            
            if q.question_type == "mcq":
                if user_ans and user_ans.strip().lower() == q.correct_answer.strip().lower():
                    obtained_marks += int(q.marks)
                    marks_for_this_q = int(q.marks)
                    is_correct = True
            else:
                has_short = True

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
        log_activity(f"Deleted exam: {exam.title}") #📜
    return redirect("/admin-dashboard")

@app.route("/create-exam-page")
def create_exam_page():
    exams = Exam.query.all()
    return render_template("create_exam.html", exams=exams)

@app.route("/assign-exam", methods=["POST"])
def assign_exam():
    exam_id = request.form.get("exam_id")
    student_id = request.form.get("student_id")
    group_id = request.form.get("group_id")

    if not exam_id:
        flash("Please select exam")
        return redirect("/admin-dashboard")

    if student_id:
        existing = ExamAssignment.query.filter_by(exam_id=exam_id, student_id=student_id).first()
        if not existing:
            assign = ExamAssignment(exam_id=exam_id, student_id=student_id)
            db.session.add(assign)

    if group_id:
        existing = ExamAssignment.query.filter_by(exam_id=exam_id, group_id=group_id).first()
        if not existing:
            assign = ExamAssignment(exam_id=exam_id, group_id=group_id)
            db.session.add(assign)

    if not student_id and not group_id:
        flash("Please select student or group")
        return redirect("/admin-dashboard")

    db.session.commit()
    flash("Exam assigned successfully")
    log_activity(f"Assigned Exam ID {exam_id} to students/groups") #📜
    return redirect("/admin-dashboard")

@app.route("/clear-assignment/<int:exam_id>")
def clear_assignment(exam_id):
    assignments = ExamAssignment.query.filter_by(exam_id=exam_id).all()
    for a in assignments:
        db.session.delete(a)
    db.session.commit()
    flash("Assignments cleared")
    log_activity(f"Cleared all assignments for Exam ID: {exam_id}") #📜
    return redirect("/admin-dashboard")


@app.route("/add-question/<int:exam_id>", methods=["GET","POST"])
def add_question(exam_id):
    questions = Question.query.filter_by(exam_id=exam_id).all()

    if request.method == "POST":
        question_text = request.form.get("question_text")
        question_type = request.form.get("question_type")
        option_a = request.form.get("option_a") 
        option_b = request.form.get("option_b")
        option_c = request.form.get("option_c")
        option_d = request.form.get("option_d")
        correct_answer = request.form.get("correct_answer")
        marks = request.form.get("marks")

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

        question = Question(
            exam_id=exam_id,
            question_text=question_text,
            question_type=question_type,
            option_a=option_a, 
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            marks=marks
        )
        db.session.add(question)
        db.session.commit()
        log_activity(f"Added a {question_type} question to Exam ID: {exam_id}") #📜
        return redirect(f"/add-question/{exam_id}")
    
    return render_template("add_question.html", exam_id=exam_id, questions=questions)


@app.route("/delete-question/<int:id>/<int:exam_id>", methods=["POST"])
def delete_question(id, exam_id):
    q = Question.query.get(id)
    if q:
        db.session.delete(q)
        db.session.commit()
        flash("Question deleted!")
        log_activity(f"Deleted a question from Exam ID: {exam_id}") #📜
    return redirect(f"/add-question/{exam_id}")


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
        log_activity(f"Updated question details for Question ID: {question_id}") #📜
        return redirect(f"/add-question/{question.exam_id}")

    return render_template("edit_question.html", q=question)


@app.route("/exam-instruction/<int:exam_id>")
def exam_instruction(exam_id):
    if "student_id" not in session:
        return redirect("/login")
    
    exam = Exam.query.get_or_404(exam_id)
    student = Student.query.get(session["student_id"])
    
    has_submitted = Result.query.filter_by(student_id=student.id, exam_id=exam.id).first()
    if has_submitted:
        flash("You have already submitted this exam!")
        return redirect("/student-dashboard")

    return render_template("exam_instruction.html", exam=exam, student=student)


@app.route("/admin-results")
def admin_results_view():
    results = Result.query.all()
    return render_template("admin_results.html", results=results) 


@app.route("/profile")
def profile():
    if "student_id" not in session:
        return redirect("/login")
    
    student = Student.query.get(session["student_id"])
    total_exams = Result.query.filter_by(student_id=student.id).count()
    return render_template("profile.html", student=student, total_exams=total_exams)


@app.route("/question-bank")
def view_question_bank():
    all_questions = Question.query.all()
    return render_template("question_bank.html", questions=all_questions)


@app.route('/students')
def view_students():
    all_students = Student.query.all()
    all_groups = Group.query.all()
    return render_template('students.html', students=all_students, groups=all_groups)


@app.route("/settings")
def admin_settings_page():
    return render_template("settings.html")


@app.route('/update-student-group/<int:id>', methods=['POST'])
def update_student_group(id):
    student = Student.query.get_or_404(id)
    new_group_id = request.form.get('group_id')
    
    student.group_id = new_group_id if new_group_id else None
    db.session.commit()

    log_activity(f"Changed group for Student: {student.name}") #📜
    return redirect('/students')


@app.route("/toggle-publish/<int:exam_id>", methods=["GET", "POST"])
def toggle_publish(exam_id):
    if "admin_id" not in session:
        return redirect("/login")
        
    exam = Exam.query.get_or_404(exam_id)
    
    if exam.is_published:
        status_text = "Hidden"
        emoji = "🙈"
    else:
        status_text = "Published"
        emoji = "📢"
    
    exam.is_published = not exam.is_published
    db.session.commit()

    log_activity(f"{status_text} the exam: '{exam.title}' {emoji}") #📜
    flash(f"Exam {status_text} successfully!", "success")
    return redirect(request.referrer or "/admin-dashboard")

@app.route("/submit-exam/<int:exam_id>", methods=["POST"])
def submit_exam(exam_id):
    if "student_id" not in session:
        return redirect("/login")

    student_id = session["student_id"]
    existing = Result.query.filter_by(student_id=student_id, exam_id=exam_id).first()

    if existing:
        flash("You have already submitted this exam!")
        return redirect("/student-dashboard")

    questions = Question.query.filter_by(exam_id=exam_id).all()
    exam = Exam.query.get(exam_id) 

    total_marks = 0
    obtained_marks = 0
    has_short = False

    for q in questions:
        user_ans = request.form.get(f"q_{q.id}") # ✅ Fix: q{q.id} থেকে q_{q.id} করা হয়েছে 
        total_marks += int(q.marks)

        is_correct = False
        marks_for_this_q = 0

        if q.question_type == "mcq":
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


@app.route("/my-results")
def my_results():
    if "student_id" not in session: 
        return redirect("/login")
    student_id = session["student_id"]
    
    student = Student.query.get(student_id) 
    
    if not student:
        session.clear()
        return redirect("/")
    
    results = Result.query.filter_by(student_id=student_id).all()
    
    exams_data = []
    chart_labels = []
    chart_scores = []
    evaluated_count = 0
    pending_count = 0

    for r in results:
        exam = Exam.query.get(r.exam_id)
        exams_data.append({"result": r, "exam": exam})
        
        chart_labels.append(exam.title)
        if exam.is_published and r.score is not None:
            chart_scores.append(r.score)
        else:
            chart_scores.append(0) 
            
        if r.status == "Evaluated":
            evaluated_count += 1
        else:
            pending_count += 1

    return render_template("my_results.html", 
                           student=student,
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
    student = Student.query.get(student_id)
    
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


@app.route("/admin/history")
def admin_history():
    if session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect("/login")
    
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template("admin_history.html", logs=logs)


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
    
    student = Student.query.get(result.student_id)
    exam = Exam.query.get(result.exam_id)
    
    answers = StudentAnswer.query.filter_by(
        student_id=result.student_id, 
        exam_id=result.exam_id
    ).all()
    
    print(f"--- DEBUG INFO ---")
    print(f"Exam ID: {result.exam_id}, Student ID: {result.student_id}")
    print(f"Answers Found: {len(answers)}")
    
    return render_template("admin_student_submission.html", 
                           result=result, student=student, 
                           exam=exam, answers=answers)


@app.route("/admin/evaluate-submission/<int:result_id>", methods=["POST"])
def evaluate_submission(result_id):
    if "admin_id" not in session:
        return redirect("/admin-login")

    result = Result.query.get_or_404(result_id)
    answers = StudentAnswer.query.filter_by(student_id=result.student_id, exam_id=result.exam_id).all()
    
    for ans in answers:
        if ans.question.question_type == "short":
            mark_input = request.form.get(f"mark_{ans.id}")
            if mark_input is not None and mark_input.strip() != "":
                ans.marks_obtained = float(mark_input)
                ans.is_correct = True if float(mark_input) > 0 else False

    total_score = sum(ans.marks_obtained for ans in answers if ans.marks_obtained is not None)
    
    result.score = total_score
    result.status = "Evaluated"
    db.session.commit()
    
    flash("Evaluation saved successfully!", "success")
    log_activity(f"Evaluated submission for Student ID: {result.student_id}") #📜
    return redirect(f"/admin/exam-results/{result.exam_id}")


with app.app_context():
    db.create_all() 
    
    admin = Admin.query.filter_by(username='teacher').first()
    if not admin:
        new_admin = Admin(username='teacher', password=generate_password_hash('1234'))
        db.session.add(new_admin)
        db.session.commit()
        print("Admin created automatically!")

if __name__ == '__main__': 
    app.run(debug=True)