from flask import Flask, render_template, request, redirect, flash
from models import db, Student, Exam, ExamAssignment

app = Flask(__name__)
app.secret_key = "secretkey"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin-dashboard")
def admin_dashboard():
    exams = Exam.query.all()
    students = Student.query.all()
    return render_template(
        "admin_dashboard.html",
        exams=exams,
        students=students
    )


# -----------------------------
# ASSIGN EXAM (Individual or Group)
# -----------------------------
@app.route("/assign-exam", methods=["POST"])
def assign_exam():
    exam_id = request.form.get("exam_id")
    student_id = request.form.get("student_id")
    group_name = request.form.get("group_name")

    # Assign to individual student
    if student_id:
        new_assignment = ExamAssignment(
            exam_id=exam_id,
            student_id=student_id
        )
        db.session.add(new_assignment)

    # Assign to group of students
    if group_name:
        group_students = Student.query.filter_by(
            group_name=group_name
        ).all()

        for student in group_students:
            new_assignment = ExamAssignment(
                exam_id=exam_id,
                student_id=student.id
            )
            db.session.add(new_assignment)

    db.session.commit()
    flash("Exam assigned successfully!")
    return redirect("/admin-dashboard")


if __name__ == "__main__":
    app.run(debug=True)