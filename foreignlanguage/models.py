import json
from foreignlanguage import db, app
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, Text, ForeignKeyConstraint
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from enum import Enum as ValueEnum
from flask_login import UserMixin


class UserRole(ValueEnum):
    STUDENT = 1
    ADMIN = 2
    CASHIER = 3
    TEACHER = 4


class MethodEnum(ValueEnum):
    CASH = 1
    BANKING = 2
    QR_CODE = 3


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

class AcademicStatus(ValueEnum):
    PENDING = 1
    PASSED = 2
    FAILED = 3

class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    joined_date = Column(DateTime, default=datetime.now)
    active = Column(Boolean, default=True)

    def __str__(self):
        return getattr(self, "name", f"{self.__class__.__name__}({self.id})")


class UserAccount(Base, UserMixin):
    name = Column(String(50))
    username = Column(String(30), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    address = Column(String(200))
    phone_num = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    avatar = Column(String(300),
                    default="https://res.cloudinary.com/desvczltb/image/upload/v1764816296/smiley-face-20_tifcgk.svg")


class EmployeeInfo(Base):
    base_salary = Column(Float, default=0.0)

    u_id = Column(Integer, ForeignKey("user_account.id"), nullable=False, unique=True)

    account = relationship('UserAccount', backref='emp_info', lazy=True)
    certifications = relationship('Certification', backref='employee', lazy=True)
    classrooms = relationship('Classroom', backref='employee', lazy=True)


class StudentInfo(Base):
    entry_score = Column(Float, default=0.0)

    u_id = Column(Integer, ForeignKey("user_account.id"), nullable=False, unique=True)

    account = relationship('UserAccount', backref='student_info', lazy=True)
    sessions = relationship('Present', back_populates='student', lazy=True)
    classes = relationship('Registration', back_populates='student', lazy=True)


class Course(Base):
    name = Column(String(50))
    description = Column(Text)
    period = Column(Float, default=0.0)
    content = Column(String(500), nullable=False)

    levels = relationship('CourseLevel', back_populates='course', lazy=True)


class Level(Base):
    name = Column(String(50))
    description = Column(Text)
    courses = relationship('CourseLevel', back_populates='level', lazy=True)

class CourseLevel(db.Model):
    __tablename__ = 'course_level'
    course_id = Column(Integer, ForeignKey("course.id"), nullable=False, primary_key=True)
    level_id = Column(Integer, ForeignKey("level.id"), nullable=False, primary_key=True)
    tuition = Column(Float, default=0.0)

    course = relationship('Course', back_populates='levels')
    level = relationship('Level', back_populates='courses')
    classrooms=relationship('Classroom', backref='course_level', lazy=True)

class Classroom(Base):  # main model
    start_time = Column(DateTime)
    maximum_stu = Column(Integer, default=25)

    employee_id = Column(Integer, ForeignKey('employee_info.id'))
    course_id = Column(Integer, nullable=False)
    level_id = Column(Integer, nullable=False)
    __table_args__ = (
        ForeignKeyConstraint(
            ['course_id', 'level_id'],
            ['course_level.course_id', 'course_level.level_id']
        ),
    )

    sessions = relationship('Session', backref='classroom', lazy=True)
    studs = relationship('Registration', back_populates='classroom', lazy=True)


class GradeCategory(Base):  # main model
    name = Column(String(50))
    weight = Column(Float, default=0.0)

    scores = relationship('Score', backref='grade_category', lazy=True)


class Certification(Base):
    name = Column(String(50))
    band_score = Column(Float, default=0.0)
    provided_date = Column(DateTime, nullable=False)

    employee_id = Column(Integer, ForeignKey('employee_info.id'), nullable=False)




class Registration(Base):
    paid = Column(Float, default=0.0)
    transact_time = Column(DateTime, default=datetime.now)
    actual_tuition = Column(Float, default=0.0)
    status = Column(Enum(StatusTuition), default=StatusTuition.UNPAID)
    final_score = Column(Float, nullable=True)
    academic_status = Column(Enum(AcademicStatus), default=AcademicStatus.PENDING)

    student_id = Column(Integer, ForeignKey('student_info.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classroom.id'), nullable=False)

    classroom = relationship('Classroom', back_populates='studs', lazy=True)
    student = relationship('StudentInfo', back_populates='classes', lazy=True)


class Transaction(Base):
    money = Column(Float, nullable=False)
    content = Column(String(500))
    method = Column(Enum(MethodEnum), default=MethodEnum.BANKING)
    date = Column(DateTime, default=datetime.now)
    status = Column(Enum(StatusPayment), default=StatusPayment.PENDING)

    employee_id = Column(Integer, ForeignKey('employee_info.id'))
    regis_id = Column(Integer, ForeignKey('registration.id'), nullable=False)

    employee = relationship('EmployeeInfo', backref='transactions', lazy=True)
    registration = relationship('Registration', backref='transactions', lazy=True)


class Session(Base):
    session_date = Column(DateTime)
    session_content = Column(String(500), nullable=False)
    shift = Column(Integer, default=0)

    class_id = Column(Integer, ForeignKey('classroom.id'), nullable=False)

    students = relationship('Present', back_populates='session', lazy=True)


class Present(db.Model):  # relationship
    is_present = Column(Boolean, default=True)

    session_id = Column(Integer, ForeignKey('session.id'), nullable=False, primary_key=True)
    student_id = Column(Integer, ForeignKey('student_info.id'), nullable=False, primary_key=True)

    session = relationship('Session', back_populates='students', lazy=True)
    student = relationship('StudentInfo', back_populates='sessions', lazy=True)


class Score(Base):
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
    # 1. Account
    try:
        with open("data/user_account.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if 'role' in p: p['role'] = UserRole[p['role'].upper()]
                if not UserAccount.query.filter_by(id=p.get('id')).first():
                    db.session.add(UserAccount(**p))
    except FileNotFoundError:
        print("Khong tim thay file data/user_account.json")

    # 2. Student
    try:
        with open("data/student_info.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if not StudentInfo.query.filter_by(id=p.get('id')).first():
                    db.session.add(StudentInfo(**p))
    except FileNotFoundError:
        print("Loi trong khi import file data/student_info.json")

    # 2. Employee
    try:
        with open("data/employee_info.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if not EmployeeInfo.query.filter_by(id=p.get('id')).first():
                    db.session.add(EmployeeInfo(**p))
    except FileNotFoundError:
        print("Loi trong khi import file data/employee_info.json")

    # 3. Course
    try:
        with open("data/course.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if not Course.query.filter_by(id=p.get('id')).first():
                    db.session.add(Course(**p))
    except FileNotFoundError:
        print("Loi trong khi import file data/course.json")

    # 4. Level
    try:
        with open("data/level.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if not Level.query.filter_by(id=p.get('id')).first():
                    db.session.add(Level(**p))
    except FileNotFoundError:
        print("Loi trong khi import file data/level.json")

    try:
        with open("data/course_level.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                exists = CourseLevel.query.filter_by(course_id=p['course_id'], level_id=p['level_id']).first()
                if not exists:
                    db.session.add(CourseLevel(**p))
    except FileNotFoundError:
        print("Khong tim thay file data/course_level.json")


    # 5. Grade Category
    try:
        with open("data/grade_category.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'joined_date' in p: p['joined_date'] = to_date(p['joined_date'])
                if not GradeCategory.query.filter_by(id=p.get('id')).first():
                    db.session.add(GradeCategory(**p))
    except FileNotFoundError:
        print("Loi trong khi import file data/grade_category.json")

    db.session.commit()
    print("Da import xong dot 1 (User, Course, Level, GradeCategory, CourseLevel)")

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
        print("Loi trong khi import file data/certificate.json")

    # 7. Classroom
    try:
        with open("data/class_room.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'start_time' in p: p['start_time'] = to_date(p['start_time'])
                if not Classroom.query.filter_by(id=p.get('id')).first():
                    db.session.add(Classroom(**p))
    except FileNotFoundError:
        print("Loi trong khi import file data/class_room.json")

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
        print("Loi trong khi import file data/registration.json")

    # 9. Session
    try:
        with open("data/session.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if 'session_date' in p: p['session_date'] = to_date(p['session_date'])
                if not Session.query.filter_by(id=p.get('id')).first():
                    db.session.add(Session(**p))
    except FileNotFoundError:
        print("Loi trong khi import file data/session.json")

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
        print("loi trong khi import file data/transaction.json")

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
        print("Loi trong khi import file data/present.json")

    # 12. Score
    try:
        with open("data/score.json", encoding="utf-8") as f:
            data = json.load(f)
            for p in data:
                if not Score.query.filter_by(id=p.get('id')).first():
                    db.session.add(Score(**p))
    except FileNotFoundError:
        print("loi trong khi import file data/score.json")

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
