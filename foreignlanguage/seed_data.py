import json
from datetime import datetime
# Import app, db và các class từ file foreignlanguage.py
from models import (
    app, db, Employee, Student, Course, Level, GradeCategory, Certification,
    Classroom, Registration, Transaction, Session, Present, Score,
    UserRole, MethodEnum, StatusPayment, StatusTuition
)

def to_date(date_str):
    if not date_str: return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def seed_data():
    print("Bat dau import du lieu...")

    # 1. Employee
    with open("data/employee.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
            # .upper() de dam bao khong loi chu hoa/thuong
            if 'role' in p: p['role'] = UserRole[p['role'].upper()]
            db.session.add(Employee(**p))

    # 2. Student
    with open("data/student.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
            if 'role' in p: p['role'] = UserRole[p['role'].upper()]
            db.session.add(Student(**p))

    # 3. Course
    with open("data/course.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
            db.session.add(Course(**p))

    # 4. Level
    with open("data/level.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
            db.session.add(Level(**p))

    # 5. Grade Category
    with open("data/grade_category.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
            db.session.add(GradeCategory(**p))

    db.session.commit()
    print("Da import xong dot 1 (Employee, Student, Course, Level, GradeCategory)")

    # 6. Certification
    with open("data/certificate.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'provided_date' in p: p['provided_date'] = to_date(p['provided_date'])
            if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
            db.session.add(Certification(**p))

    # 7. Classroom
    with open("data/class_room.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'start_time' in p: p['start_time'] = to_date(p['start_time'])
            db.session.add(Classroom(**p))

    db.session.commit()
    print("Da import xong dot 2 (Certification, Classroom)")

    # 8. Registration
    with open("data/registration.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'transact_time' in p: p['transact_time'] = to_date(p['transact_time'])
            if 'status' in p: p['status'] = StatusTuition[p['status'].upper()]
            db.session.add(Registration(**p))

    # 9. Session
    with open("data/session.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'session_date' in p: p['session_date'] = to_date(p['session_date'])
            db.session.add(Session(**p))

    db.session.commit()
    print("Da import xong dot 3 (Registration, Session)")

    # 10. Transaction
    with open("data/transaction.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            if 'date' in p: p['date'] = to_date(p['date'])
            if 'method' in p: p['method'] = MethodEnum[p['method'].upper()]
            if 'status' in p: p['status'] = StatusPayment[p['status'].upper()]
            db.session.add(Transaction(**p))

    # 11. Present
    with open("data/present.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            db.session.add(Present(**p))

    # 12. Score
    with open("data/score.json", encoding="utf-8") as f:
        data = json.load(f)
        for p in data:
            db.session.add(Score(**p))

    db.session.commit()
    print("HOAN TAT: Da import toan bo du lieu thanh cong.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        try:
            seed_data()
        except Exception as e:
            print(f"CO LOI XAY RA: {e}")
            db.session.rollback()