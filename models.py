from flask_sqlalchemy import SQLAlchemy
from flask import session
from datetime import datetime

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
    password = db.Column(db.String(255))
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"))

# -----------------------------
# ADMIN TABLE
# -----------------------------
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) 

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
    @property
    def question_count(self):
        return len(self.questions)
    
    
# -----------------------------
# RESULT TABLE
# -----------------------------
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    score = db.Column(db.Integer)
    is_published = db.Column(db.Boolean, default=False) # রেজাল্ট পাবলিশ করার জন্য
    status = db.Column(db.String(20), default="Evaluated")
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

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
# STUDENT ANSWER TABLE
# -----------------------------
class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    user_answer = db.Column(db.String(1000))
    marks_obtained = db.Column(db.Float, default=0) # মার্কস ডেসিমাল হতে পারে
    is_correct = db.Column(db.Boolean, default=False)
    question = db.relationship("Question", backref="student_answers")

# -----------------------------
# ACTIVITY LOG TABLE
# -----------------------------
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True) # nullable True দেওয়া ভালো
    action = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship('Admin', backref='logs')

# -----------------------------
# HELPER FUNCTION
# -----------------------------
def log_activity(action_text):
    admin_id = session.get('admin_id')
    # সেশনে admin_id না থাকলে সরাসরি 'admin' কি চেক করবে
    if not admin_id and 'admin' in session:
        # যদি সেশনে শুধু ইউজারনেম থাকে, তবে ডাটাবেস থেকে আইডি খুঁজে নেবে
        from models import Admin
        admin_obj = Admin.query.filter_by(username=session['admin']).first()
        admin_id = admin_obj.id if admin_obj else None

    new_log = ActivityLog(admin_id=admin_id, action=action_text)
    db.session.add(new_log)
    db.session.commit()