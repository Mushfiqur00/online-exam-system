from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -----------------------------
# GROUP TABLE
# -----------------------------
class Group(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    code = db.Column(db.String(10), unique=True)


# -----------------------------
# STUDENT TABLE
# -----------------------------
class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    student_id = db.Column(db.String(50), unique=True)

    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

    group_id = db.Column(db.Integer, db.ForeignKey("group.id"))


# -----------------------------
# EXAM TABLE
# -----------------------------
class Exam(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100))
    exam_date = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    duration = db.Column(db.Integer)


# -----------------------------
# EXAM ASSIGNMENT TABLE
# -----------------------------
class ExamAssignment(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

    student = db.relationship("Student", backref="assignments")
    group = db.relationship("Group", backref="assignments")


# =====================================================
# SHUBROTO FEATURE
# Admin can create MCQ / Short questions and set marks
# =====================================================
class Question(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"))

    question_text = db.Column(db.String(500))

    # mcq / short
    question_type = db.Column(db.String(20))

    option1 = db.Column(db.String(200))
    option2 = db.Column(db.String(200))
    option3 = db.Column(db.String(200))
    option4 = db.Column(db.String(200))

    correct_answer = db.Column(db.String(200))

    # marks for each question
    marks = db.Column(db.Integer)