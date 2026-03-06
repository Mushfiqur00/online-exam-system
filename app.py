from flask import Flask, render_template
from datetime import date
from models import db, Exam

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///exam.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/student-dashboard")
def student_dashboard():

    today = date.today()
    exams = Exam.query.all()

    upcoming = []
    ongoing = []
    completed = []

    for exam in exams:

        if exam.exam_date > today:
            upcoming.append(exam)

        elif exam.exam_date == today:
            ongoing.append(exam)

        else:
            completed.append(exam)

    return render_template(
        "student_dashboard.html",
        upcoming=upcoming,
        ongoing=ongoing,
        completed=completed
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)