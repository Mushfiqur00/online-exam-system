from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -----------------------------
# GROUP TABLE
# -----------------------------
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    code = db.Column(db.String(10), unique=True)
    students = db.relationship('Student', backref='group', lazy=True)

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
    is_published = db.Column(db.Boolean, default=False) 
    
    questions = db.relationship('Question', backref='exam', cascade="all, delete-orphan", lazy=True)

# -----------------------------
# RESULT TABLE (Combined Feature 1 & 4)
# -----------------------------
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    score = db.Column(db.Integer)
    is_published = db.Column(db.Boolean, default=False) # Feature 4
    status = db.Column(db.String(20), default="Evaluated") # Feature 1

# -----------------------------
# EXAM ASSIGNMENT TABLE
# -----------------------------
class ExamAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)

    student = db.relationship("Student", backref="assignments")
    group = db.relationship("Group", backref="assignments")
    exam = db.relationship("Exam", backref="assignments")

# -----------------------------
# QUESTION TABLE
# -----------------------------
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"))
    question_text = db.Column(db.String(500))
    question_type = db.Column(db.String(20)) # mcq / short
    option_a = db.Column(db.String(200))
    option_b = db.Column(db.String(200))
    option_c = db.Column(db.String(200))
    option_d = db.Column(db.String(200))
    correct_answer = db.Column(db.String(200))
    marks = db.Column(db.Integer)

# -----------------------------
# STUDENT ANSWER TABLE (New)
# -----------------------------
class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    user_answer = db.Column(db.String(1000))
    marks_obtained = db.Column(db.Integer, default=0)
    is_correct = db.Column(db.Boolean, default=False)
    question = db.relationship("Question", backref="student_answers")