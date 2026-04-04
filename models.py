from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -----------------------------
# GROUP TABLE
# -----------------------------
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    code = db.Column(db.String(10), unique=True)
    
    # ব্যাকরেফারেন্স যোগ করা হয়েছে যাতে group.students দিয়ে সব স্টুডেন্ট পাওয়া যায়
    students = db.relationship('Student', backref='group', lazy=True)

# -----------------------------
# STUDENT TABLE
# -----------------------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    student_id = db.Column(db.String(50), unique=True) # Institutional ID
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
    
    # পরীক্ষার সব প্রশ্ন সহজে পাওয়ার জন্য রিলেশনশিপ
    questions = db.relationship('Question', backref='exam', cascade="all, delete-orphan", lazy=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    score = db.Column(db.Integer)
    
    # নতুন ফিল্ড: পরীক্ষার রেজাল্ট পাবলিশ হয়েছে কি না (Feature 4 এর জন্য)
    is_published = db.Column(db.Boolean, default=False)
    
    # নতুন ফিল্ড: শর্ট কোশ্চেন থাকলে স্ট্যাটাস 'Pending' হবে, না হলে 'Evaluated'
    status = db.Column(db.String(20), default="Evaluated")

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
# QUESTION TABLE (Updated for consistency)
# -----------------------------
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"))
    question_text = db.Column(db.String(500))
    question_type = db.Column(db.String(20)) # mcq / short

    # অপশনগুলোর নাম admin_layout/edit_question এর সাথে মিল রেখে পরিবর্তন করা হয়েছে
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
    
    # স্টুডেন্টের দেওয়া উত্তর (MCQ এর ক্ষেত্রে অপশন, Short এর ক্ষেত্রে টেক্সট)
    user_answer = db.Column(db.String(1000))
    
    # এই নির্দিষ্ট প্রশ্নে কত মার্কস পেল (MCQ হলে অটো, Short হলে পরে অ্যাডমিন দিবে)
    marks_obtained = db.Column(db.Integer, default=0)
    
    # উত্তরটি সঠিক কি না (MCQ এর জন্য)
    is_correct = db.Column(db.Boolean, default=False)

    question = db.relationship("Question", backref="student_answers")

    # --- Rakibul's Code: Feature 1 & 4 (Models) ---
# --- Rakibul's Code: Feature 1 & 4 (Models) ---

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    score = db.Column(db.Integer)
    # Feature 4: Admin can publish/hide
    is_published = db.Column(db.Boolean, default=False) 
    # Feature 1: Evaluation Status
    status = db.Column(db.String(20), default="Evaluated") 

class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    user_answer = db.Column(db.String(1000))
    marks_obtained = db.Column(db.Integer, default=0)
    is_correct = db.Column(db.Boolean, default=False)
    question = db.relationship("Question", backref="student_answers")