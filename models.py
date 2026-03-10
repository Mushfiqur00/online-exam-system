from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# -------------------
# Group Model
# -------------------
class Group(db.Model):
    __tablename__ = "group"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Group {self.name}>"


# -------------------
# Student Model
# -------------------
class Student(db.Model):
    __tablename__ = "student"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)

    group_id = db.Column(db.Integer, db.ForeignKey("group.id"))

    def __repr__(self):
        return f"<Student {self.username}>"


# -------------------
# Exam Model
# -------------------
class Exam(db.Model):
    __tablename__ = "exam"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

    exam_date = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    duration = db.Column(db.Integer)

    def __repr__(self):
        return f"<Exam {self.title}>"


# -------------------
# Exam Assignment
# -------------------
class ExamAssignment(db.Model):
    __tablename__ = "exam_assignment"

    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(db.Integer, db.ForeignKey("exam.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"))
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"))

    def __repr__(self):
        return f"<Assignment Exam:{self.exam_id}>"