from foreignlanguage.models import Student, UserRole, Employee, Course
from foreignlanguage import app, db
import hashlib

def auth_user(username,password, role):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    if int(role).__eq__(UserRole.STUDENT.value):
        return Student.query.filter(Student.username.__eq__(username), Student.password.__eq__(password)).first()
    else:
        return Employee.query.filter(Employee.username.__eq__(username), Employee.password.__eq__(password)).first()

def add_user(username, password, email, address):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    u = Student(username=username, password=password, email=email, address=address)
    db.session.add(u)
    db.session.commit()

def check_email(email):
    return Student.query.filter(Student.email.__eq__(email)).first()

def get_user_by_id(uid, role):
    if role == UserRole.STUDENT.name:
        return Student.query.get(uid)
    else:
        return Employee.query.get(uid)

def get_user_by_username(username):
    return Student.query.filter(Student.username == username).first()

def load_user_roles():
    return [role for role in UserRole if role != UserRole.ADMIN]

def load_courses():
    return Course.query.all()

def load_levels_by_course_id():
    pass

if __name__=="__main__":
    with app.app_context():
        print(auth_user("user", "123"))
        print(load_user_roles())