from flask import Flask, render_template, request, redirect, session
from datetime import datetime
from models import get_db_connection, create_tables

app = Flask(__name__)
app.secret_key = "supersecretkey"

create_tables()

# ---------------------
# LOGIN
# ---------------------
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Admin Login
        if username == "teacher" and password == "1234":
            session['role'] = "admin"
            return redirect('/admin-dashboard')

        # Student Login
        elif username == "student" and password == "group4":
            session['role'] = "student"
            return redirect('/student-dashboard')

        else:
            return "Invalid Credentials"

    return render_template('login.html')


# ---------------------
# LOGOUT
# ---------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------------
# ADMIN DASHBOARD
# ---------------------
@app.route('/admin-dashboard')
def admin_dashboard():

    if session.get('role') != "admin":
        return redirect('/')

    conn = get_db_connection()
    exams = conn.execute('SELECT * FROM exams').fetchall()
    conn.close()

    return render_template('admin_dashboard.html', exams=exams)


# ---------------------
# CREATE EXAM
# ---------------------
@app.route('/create-exam', methods=['GET', 'POST'])
def create_exam():

    if session.get('role') != "admin":
        return redirect('/')

    if request.method == 'POST':
        title = request.form['title']
        exam_date = request.form['exam_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        duration = request.form['duration']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO exams (title, exam_date, start_time, end_time, duration) VALUES (?, ?, ?, ?, ?)',
            (title, exam_date, start_time, end_time, duration)
        )
        conn.commit()
        conn.close()

        return redirect('/admin-dashboard')

    return render_template('create_exam.html')


# ---------------------
# STUDENT DASHBOARD
# ---------------------
@app.route('/student-dashboard')
def student_dashboard():

    if session.get('role') != "student":
        return redirect('/')

    conn = get_db_connection()
    exams = conn.execute('SELECT * FROM exams').fetchall()
    conn.close()

    return render_template('student_dashboard.html', exams=exams)


# ---------------------
# START EXAM (Eligibility Check)
# ---------------------
@app.route('/start-exam/<int:exam_id>')
def start_exam(exam_id):

    if session.get('role') != "student":
        return redirect('/')

    conn = get_db_connection()
    exam = conn.execute('SELECT * FROM exams WHERE id = ?', (exam_id,)).fetchone()
    conn.close()

    if exam is None:
        return "Exam not found."

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    if today < exam['exam_date']:
        return "Exam has not started yet."

    if current_time > exam['end_time']:
        return "Exam already finished."

    if exam['start_time'] <= current_time <= exam['end_time']:
        return "You can start the exam now!"

    return "You cannot access this exam at this time."


if __name__ == '__main__':
    app.run(debug=True)