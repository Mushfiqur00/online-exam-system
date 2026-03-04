from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -------------------
# Student Model
# -------------------
class Student(db.Model):
    __tablename__ = "student"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Student {self.username}>"


# -------------------
# Exam Model
# -------------------
class Exam(db.Model):
    __tablename__ = "exam"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Exam {self.title}>"

class ExamAssignment(db.Model):
    __tablename__ = "exam_assignment"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))