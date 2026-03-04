from flask import Flask, render_template, request, redirect
from datetime import datetime
from models import get_db_connection, create_tables

app = Flask(__name__)

# Create tables when app starts
create_tables()

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