from flask import Flask, render_template, request, redirect
from datetime import datetime
from models import get_db_connection, create_tables

app = Flask(__name__)

# Create tables when app starts
create_tables()


# ----------------------
# Admin Dashboard
# ----------------------
@app.route('/admin-dashboard')
def admin_dashboard():
    conn = get_db_connection()
    exams = conn.execute('SELECT * FROM exams').fetchall()
    conn.close()

    return render_template('admin_dashboard.html', exams=exams)


# ----------------------
# Create Exam
# ----------------------
@app.route('/create-exam', methods=['GET', 'POST'])
def create_exam():
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


# ----------------------
# Student Dashboard
# ----------------------
@app.route('/student-dashboard')
def student_dashboard():
    conn = get_db_connection()
    exams = conn.execute('SELECT * FROM exams').fetchall()
    conn.close()

    return render_template('student_dashboard.html', exams=exams)


# ----------------------
# Start Exam (Eligibility Check)
# ----------------------
@app.route('/start-exam/<int:exam_id>')
def start_exam(exam_id):

    conn = get_db_connection()
    exam = conn.execute('SELECT * FROM exams WHERE id = ?', (exam_id,)).fetchone()
    conn.close()

    if exam is None:
        return "Exam not found"

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