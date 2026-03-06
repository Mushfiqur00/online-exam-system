from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    exam_date = db.Column(db.Date, nullable=False)
    exam_time = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer)
    total_marks = db.Column(db.Integer)

    def __repr__(self):
        return f"<Exam {self.subject}>"