from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

def setup_database():
    with app.app_context():
        # ১. সব টেবিল তৈরি করবে (যদি না থাকে)
        db.create_all()
        
        # ২. চেক করবে 'teacher' নামে কোনো অ্যাডমিন অলরেডি আছে কি না
        admin_exists = Admin.query.filter_by(username='teacher').first()
        
        if not admin_exists:
            # অ্যাডমিন না থাকলে নতুন করে তৈরি করবে
            hashed_pw = generate_password_hash('1234')
            default_admin = Admin(username='teacher', password=hashed_pw)
            db.session.add(default_admin)
            db.session.commit()
            print("✅ Default Admin 'teacher' created successfully!")
        else:
            print("ℹ️ Admin already exists. No changes made.")

if __name__ == "__main__":
    setup_database()