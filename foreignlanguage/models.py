from foreignlanguage import db, app
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from enum import Enum as ValueEnum


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
    CANCELED = 4


class StatusTuition(ValueEnum):
    UNPAID = 1
    PAID = 2
    PARTIAL = 3
    OVERDUE = 4


class Base(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    name = Column(String(50), nullable=False)
    joined_date = Column(DateTime, default=datetime.now)
    active = Column(Boolean, default=True)


class User(Base):
    __abstract__ = True
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    address = Column(String(200))
    phone_num = Column(String(20))
    role = Column(Enum(UserRole), default=UserRole.STUDENT)


class Employee(User):
    base_salary = Column(Float, default=0.0)


class Student(User):
    entry_score = Column(Float, default=0.0)


class Course(Base):
    description = Column(String(500))
    period = Column(Float, default=0.0)
    content = Column(String(500), nullable=False)


class Level(Base):
    tuition = Column(Float, default=0.0)


class GradeCategory(Base):
    weight = Column(Float, default=0.0)


class Certificate(Base):
    band_score = Column(Float, default=0.0)
    provided_date = Column(DateTime, nullable=False)
    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)


class ClassRoom(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    start_time = Column(DateTime, nullable=False)
    maximum_stu = Column(Integer, default=25)
    employee_id = Column(Integer, ForeignKey('employee.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    level_id = Column(Integer, ForeignKey('level.id'), nullable=False)


class Registration(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    paid = Column(Float, default=0.0)
    transact_time = Column(DateTime, default=datetime.now)
    actual_tuition = Column(Float, default=0.0)
    status = Column(Enum(StatusTuition), default=StatusTuition.UNPAID)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('class_room.id'), nullable=False)


class Transaction(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    money = Column(Float, nullable=False)
    content = Column(String(500))
    method = Column(Enum(MethodEnum), default=MethodEnum.BANKING)
    date = Column(DateTime, default=datetime.now)
    status = Column(Enum(StatusPayment), default=StatusPayment.PENDING)
    employee_id = Column(Integer, ForeignKey('employee.id'))
    regis_id = Column(Integer, ForeignKey('registration.id'), nullable=False)


class Session(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    session_date = Column(DateTime)
    session_content = Column(String(500), nullable=False)
    shift = Column(Integer, default=0)
    class_id = Column(Integer, ForeignKey('class_room.id'), nullable=False)


class Present(db.Model):
    is_present = Column(Boolean, default=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False, primary_key=True)
    student_id = Column(Integer, ForeignKey('student.id'), nullable=False, primary_key=True)


class Score(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False, unique=True)
    value = Column(Float, default=0.0)
    regis_id = Column(Integer, ForeignKey('registration.id'), nullable=False)
    grade_cate_id = Column(Integer, ForeignKey('grade_category.id'), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.commit()

