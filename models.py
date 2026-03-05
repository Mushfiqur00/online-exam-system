from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()


# -----------------------------
# EXAM TABLE (Your Feature)
# -----------------------------
class Exam(db.Model):
    __tablename__ = "exam"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    exam_date = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    duration = db.Column(db.Integer)