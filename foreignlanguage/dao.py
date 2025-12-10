from sqlalchemy import desc, or_
from foreignlanguage.models import Student, UserRole, Employee, Course, Registration, Transaction, StatusTuition, \
    StatusPayment
from foreignlanguage import app, db
import hashlib


def auth_user(username, password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()

    emp = Employee.query.filter(Employee.username.__eq__(username),
                                Employee.password.__eq__(password)).first()
    if emp:
        return emp

    stu = Student.query.filter(Student.username.__eq__(username),
                               Student.password.__eq__(password)).first()
    return stu

def add_user(username, password, email, address):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    u = Student(username=username, password=password, email=email, address=address)
    db.session.add(u)
    db.session.commit()

def check_email(email):
    return Student.query.filter(Student.email.__eq__(email)).first()


def get_user_by_id(uid):
    user = Employee.query.get(uid)
    if user:
        return user
    # Nếu không thấy thì tìm trong bảng Student
    return Student.query.get(uid)

def get_user_by_username(username):
    user = Employee.query.filter(Employee.username == username).first()
    if user:
        return user
    return Student.query.filter(Student.username == username).first()

# def load_user_roles():
#     return [role for role in UserRole if role != UserRole.ADMIN]

def load_courses():
    return Course.query.all()

def load_levels_by_course_id():
    pass

#################################
# LẤY DANH SÁCH NỢ TỪ SQL
def get_unpaid_registrations(kw=None):
    # 1. Lọc các trạng thái chưa hoàn thành
    query = Registration.query.filter(Registration.status != StatusTuition.PAID)
    if kw:
        query = query.join(Student).filter(or_(
            Student.name.contains(kw),
            Student.phone_num.contains(kw),
            Student.email.contains(kw)
        ))

    return query.all()

if __name__=="__main__":
    with app.app_context():
        print(auth_user("user", "123"))
        #print(load_user_roles())