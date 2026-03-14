from flask_sqlalchemy import SQLAlchemy
import random
import string

db = SQLAlchemy()

def generate_code():

    return ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=6
        )
    )
class Group(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    code = db.Column(db.String(10), unique=True)

class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))
    student_id = db.Column(db.String(50), unique=True)

    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

    group_id = db.Column(db.Integer, db.ForeignKey("group.id"))

    
class Exam(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100))
    exam_date = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    duration = db.Column(db.Integer)

class ExamAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

    student = db.relationship("Student", backref="assignments")
    group = db.relationship("Group", backref="assignments")