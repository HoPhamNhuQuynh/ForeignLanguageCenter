from foreignlanguage.models import User, Student
from foreignlanguage import app, db
import hashlib


def auth_user(username,password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return Student.query.filter(Student.username.__eq__(username), Student.password.__eq__(password)).first()

def add_user(phone_num, username, password, email, address):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    u = Student(phone_num=phone_num , username=username, password=password, email=email, address=address)
    db.session.add(u)
    db.session.commit()

def get_user_by_id(uid):
    return Student.query.get(uid)

def get_user_by_username(username):
    return Student.query.filter(Student.username == username).first()

if __name__=="__main__":
    with app.app_context():
        print(auth_user("user", "123"))