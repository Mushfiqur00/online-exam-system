from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------------------------
# DATABASE INITIALIZATION
# ---------------------------
def init_db():
    conn = sqlite3.connect('database.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration INTEGER NOT NULL
        )
    ''')
    conn.close()

init_db()


# ---------------------------
# SIMPLE LOGIN (NO DATABASE)
# ---------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "teacher" and password == "1234":
            return redirect('/admin-dashboard')

        elif username == "student" and password == "group4":
            return redirect('/student-dashboard')

        else:
            return "Invalid Credentials"

    return render_template('login.html')


# ---------------------------
# ADMIN DASHBOARD (DATE SORTED)
# ---------------------------
@app.route('/admin-dashboard')
def admin_dashboard():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    exams = conn.execute("""
        SELECT * FROM exams
        ORDER BY exam_date ASC, start_time ASC
    """).fetchall()

    conn.close()

    return render_template('admin_dashboard.html', exams=exams)


# ---------------------------
# CREATE EXAM (WITH CONFLICT CHECK)
# ---------------------------
@app.route('/create-exam', methods=['POST'])
def create_exam():
    title = request.form['title']
    exam_date = request.form['exam_date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    duration = request.form['duration']

    conn = sqlite3.connect('database.db')

    # CHECK FOR TIME CONFLICT ON SAME DATE
    conflict = conn.execute('''
        SELECT * FROM exams
        WHERE exam_date = ?
        AND (start_time < ? AND end_time > ?)
    ''', (exam_date, end_time, start_time)).fetchall()

    if conflict:
        conn.close()
        return "Another exam is already scheduled at this time!"

    conn.execute('''
        INSERT INTO exams (title, exam_date, start_time, end_time, duration)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, exam_date, start_time, end_time, duration))

    conn.commit()
    conn.close()

    return redirect('/admin-dashboard')


# ---------------------------
# DELETE EXAM
# ---------------------------
@app.route('/delete-exam/<int:exam_id>')
def delete_exam(exam_id):
    conn = sqlite3.connect('database.db')
    conn.execute('DELETE FROM exams WHERE id=?', (exam_id,))
    conn.commit()
    conn.close()
    return redirect('/admin-dashboard')


# ---------------------------
# STUDENT DASHBOARD (DATE SORTED)
# ---------------------------
@app.route('/student-dashboard')
def student_dashboard():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row

    exams = conn.execute("""
        SELECT * FROM exams
        ORDER BY exam_date ASC, start_time ASC
    """).fetchall()

    conn.close()

    return render_template('student_dashboard.html', exams=exams)


# ---------------------------
# START EXAM (ELIGIBILITY CHECK)
# ---------------------------
@app.route('/start-exam/<int:exam_id>')
def start_exam(exam_id):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    exam = conn.execute("SELECT * FROM exams WHERE id=?", (exam_id,)).fetchone()
    conn.close()

    if not exam:
        return "Exam not found"

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    # Date check
    if today < exam['exam_date']:
        return "Exam not started yet"

    if today > exam['exam_date']:
        return "Exam already finished"

    # Time check
    if current_time < exam['start_time']:
        return "Exam not started yet"

    if current_time > exam['end_time']:
        return "Exam time is over"

    return f"You can start the exam: {exam['title']}"


if __name__ == '__main__':
    app.run(debug=True)