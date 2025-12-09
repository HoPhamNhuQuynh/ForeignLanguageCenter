import json
from datetime import datetime
from enum import Enum as ValueEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship, backref
from foreignlanguage import db, app

class UserRole(ValueEnum):
    STUDENT = 1
    ADMIN = 2
    CASHIER = 3
    TEACHER = 4

class MethodEnum(ValueEnum):
    CASH = 1
    BANKING = 2

class StatusPayment(ValueEnum):
    SUCCESS = 1
    FAILED = 2
    PENDING = 3
    CANCELLED = 4

class StatusTuition(ValueEnum):
    UNPAID = 1
    PAID = 2
    PARTIAL = 3
    OVERDUE = 4

class Base(db.Model):  # base model
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    name = Column(String(50))
    joined_date = Column(DateTime, default=datetime.now)
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.name

class User(Base, UserMixin):  # base model of users
    __abstract__ = True
    username = Column(String(30), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    address = Column(String(200))
    phone_num = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    avatar = Column(String(300),default="https://res.cloudinary.com/desvczltb/image/upload/v1764816296/smiley-face-20_tifcgk.svg")

class Employee(User):  # main model
    base_salary = Column(Float, default=0.0)
    certifications = relationship('Certification', backref='employee', lazy=True)
    classrooms = relationship('Classroom', backref='employee', lazy=True)

class Student(User):
    entry_score = Column(Float, default=0.0)
    sessions = relationship('Present', back_populates='student', lazy=True)
    classes = relationship('Registration', back_populates='student', lazy=True)


class Course(Base):
    description = Column(String(500))
    period = Column(Float, default=0.0)
    content = Column(String(500), nullable=False)
    classrooms = relationship('Classroom', backref='course', lazy=True)


class Level(Base):
    tuition = Column(Float, default=0.0)
    classrooms = relationship('Classroom', backref='level', lazy=True)


class GradeCategory(Base):
    weight = Column(Float, default=0.0)
    scores = relationship('Score', backref='grade_category', lazy=True)


class Certification(Base):
    band_score = Column(Float, default=0.0)
    provided_date = Column(DateTime, nullable=False)
    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)

class Classroom(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    start_time = Column(DateTime, nullable=False)
    maximum_stu = Column(Integer, default=25)
    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    level_id = Column(Integer, ForeignKey('level.id'), nullable=False)
    sessions = relationship('Session', backref='classroom', lazy=True)
    studs = relationship('Registration', back_populates='classroom')

class Registration(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    paid = Column(Float, default=0.0)
    transact_time = Column(DateTime, default=datetime.now)
    actual_tuition = Column(Float, default=0.0)
    status = Column(Enum(StatusTuition), default=StatusTuition.UNPAID)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classroom.id'), nullable=False)
    classroom = relationship('Classroom', back_populates='studs')
    student = relationship('Student', back_populates='classes')


class Transaction(db.Model):  # main model
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    money = Column(Float, nullable=False)
    content = Column(String(500))
    method = Column(Enum(MethodEnum), default=MethodEnum.BANKING)
    date = Column(DateTime, default=datetime.now)
    status = Column(Enum(StatusPayment), default=StatusPayment.PENDING)
    employee_id = Column(Integer, ForeignKey('employee.id'))
    regis_id = Column(Integer, ForeignKey('registration.id'), nullable=False)
    employee = relationship('Employee', backref='transactions', lazy=True)
    registration = relationship('Registration', backref='transactions', lazy=True)

class Session(db.Model):  # main model
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    session_date = Column(DateTime)
    session_content = Column(String(500), nullable=False)
    shift = Column(Integer, default=0)
    class_id = Column(Integer, ForeignKey('classroom.id'), nullable=False)
    students = relationship('Present', back_populates='session', lazy=True)

class Present(db.Model):  # relationship
    is_present = Column(Boolean, default=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False, primary_key=True)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False, primary_key=True)
    session = relationship('Session', back_populates='students', lazy=True)
    student = relationship('Student', back_populates='sessions', lazy=True)

class Score(db.Model):  # main model
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    value = Column(Float, default=0.0)
    regis_id = Column(Integer, ForeignKey('registration.id'), nullable=False)
    grade_cate_id = Column(Integer, ForeignKey('grade_category.id'), nullable=False)
    registration = relationship('Registration', backref='scores', lazy=True)


def to_date(date_str):
    if not date_str: return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def seed_data():
    print("Bat dau import du lieu...")
    # 1. Employee
    try:
        with open("data/employee.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if 'role' in p: p['role'] = UserRole[p['role'].upper()]
                # Kiểm tra tồn tại trước khi add để tránh duplicate
                if not Employee.query.filter_by(id=p.get('id')).first():
                    db.session.add(Employee(**p))
    except FileNotFoundError:
        print("Khong tim thay file data/employee.json, bo qua.")

    # 2. Student
    try:
        with open("data/student.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if 'role' in p: p['role'] = UserRole[p['role'].upper()]
                if not Student.query.filter_by(id=p.get('id')).first():
                    db.session.add(Student(**p))
    except FileNotFoundError:
        pass

    # 3. Course
    try:
        with open("data/course.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if not Course.query.filter_by(id=p.get('id')).first():
                    db.session.add(Course(**p))
    except FileNotFoundError:
        pass

    # 4. Level
    try:
        with open("data/level.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if not Level.query.filter_by(id=p.get('id')).first():
                    db.session.add(Level(**p))
    except FileNotFoundError:
        pass

    # 5. Grade Category
    try:
        with open("data/grade_category.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if not GradeCategory.query.filter_by(id=p.get('id')).first():
                    db.session.add(GradeCategory(**p))
    except FileNotFoundError:
        pass

    db.session.commit()
    print("Da import xong dot 1 (User, Course, Level, GradeCategory)")

    # 6. Certification
    try:
        with open("data/certificate.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'provided_date' in p: p['provided_date'] = to_date(p['provided_date'])
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if not Certification.query.filter_by(id=p.get('id')).first():
                    db.session.add(Certification(**p))
    except FileNotFoundError:
        pass

    # 7. Classroom
    try:
        with open("data/class_room.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'start_time' in p: p['start_time'] = to_date(p['start_time'])
                if not Classroom.query.filter_by(id=p.get('id')).first():
                    db.session.add(Classroom(**p))
    except FileNotFoundError:
        pass

    db.session.commit()
    print("Da import xong dot 2 (Certification, Classroom)")

    # 8. Registration
    try:
        with open("data/registration.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'transact_time' in p: p['transact_time'] = to_date(p['transact_time'])
                if 'status' in p: p['status'] = StatusTuition[p['status'].upper()]
                if not Registration.query.filter_by(id=p.get('id')).first():
                    db.session.add(Registration(**p))
    except FileNotFoundError:
        pass

    # 9. Session
    try:
        with open("data/session.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'session_date' in p: p['session_date'] = to_date(p['session_date'])
                if not Session.query.filter_by(id=p.get('id')).first():
                    db.session.add(Session(**p))
    except FileNotFoundError:
        pass

    db.session.commit()
    print("Da import xong dot 3 (Registration, Session)")

    # 10. Transaction
    try:
        with open("data/transaction.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'date' in p: p['date'] = to_date(p['date'])
                if 'method' in p: p['method'] = MethodEnum[p['method'].upper()]
                if 'status' in p: p['status'] = StatusPayment[p['status'].upper()]
                if not Transaction.query.filter_by(id=p.get('id')).first():
                    db.session.add(Transaction(**p))
    except FileNotFoundError:
        pass

    # 11. Present
    try:
        with open("data/present.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                # Bảng Present có composite primary key (session_id, student_id)
                exists = Present.query.filter_by(session_id=p['session_id'], student_id=p['student_id']).first()
                if not exists:
                    db.session.add(Present(**p))
    except FileNotFoundError:
        pass

    # 12. Score
    try:
        with open("data/score.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if not Score.query.filter_by(id=p.get('id')).first():
                    db.session.add(Score(**p))
    except FileNotFoundError:
        pass

    db.session.commit()
    print("HOAN TAT: Da import toan bo du lieu thanh cong.")

if __name__ == '__main__':
    with app.app_context():
        # Tạo bảng
        db.create_all()
        try:
            seed_data()
        except Exception as e:
            print(f"CO LOI XAY RA KHI SEED DATA: {e}")
            db.session.rollback()
