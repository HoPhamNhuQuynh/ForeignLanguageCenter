from foreignlanguage import db, app
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, values
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
    name = Column(String(50), nullable=False)
    joined_date = Column(DateTime, default=datetime.now)
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.name


class User(Base):  # base model of users
    __abstract__ = True
    username = Column(String(30), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    address = Column(String(200))
    phone_num = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.STUDENT)
    avatar = Column(String(300), default="https://res.cloudinary.com/desvczltb/image/upload/v1764816296/smiley-face-20_tifcgk.svg")


class Employee(User):  # main model
    base_salary = Column(Float, default=0.0)

    certifications = relationship('Certification', backref='employee', lazy=True)
    classrooms = relationship('Classroom', backref='employee', lazy=True)


class Student(User, UserMixin):  # main model
    entry_score = Column(Float, default=0.0)

    sessions = relationship('Present', back_populates='student', lazy=True)
    classes = relationship('Registration', back_populates='student', lazy=True)


class Course(Base):  # main model
    description = Column(String(500))
    period = Column(Float, default=0.0)
    content = Column(String(500), nullable=False)

    classrooms = relationship('Classroom', backref='course', lazy=True)


class Level(Base):  # main model
    tuition = Column(Float, default=0.0)

    classrooms = relationship('Classroom', backref='level', lazy=True)


class GradeCategory(Base):  # main model
    weight = Column(Float, default=0.0)

    scores = relationship('Score', backref='grade_category', lazy=True)


class Certification(Base):  # main model
    band_score = Column(Float, default=0.0)
    provided_date = Column(DateTime, nullable=False)

    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)


class Classroom(db.Model):  # main model
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    start_time = Column(DateTime, nullable=False)
    maximum_stu = Column(Integer, default=25)

    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    level_id = Column(Integer, ForeignKey('level.id'), nullable=False)

    sessions = relationship('Session', backref='classroom', lazy=True)
    studs = relationship('Registration', back_populates='classroom')


class Registration(db.Model):  # relationship
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

if __name__ == '__main__':
    with app.app_context():

        import hashlib

        u1 = Student(name="User", username="user", password=hashlib.md5("123".encode("utf-8")).hexdigest(), email="user@gmail.com")

        db.create_all()
        db.session.commit()
