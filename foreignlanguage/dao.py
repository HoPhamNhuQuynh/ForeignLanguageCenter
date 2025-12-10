from sqlalchemy import or_

from foreignlanguage.models import UserAccount, Course, Transaction, Registration, StatusTuition, Level
from foreignlanguage import app, db
import hashlib

def auth_user(username,password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return UserAccount.query.filter(UserAccount.username.__eq__(username), UserAccount.password.__eq__(password)).first()

def add_user(username, password, email, address):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    u = UserAccount(username=username, password=password, email=email, address=address)
    db.session.add(u)
    db.session.commit()

def update_user_password(new_password, u_id):
    new_password = hashlib.md5(new_password.encode("utf-8")).hexdigest()
    u = get_user_by_id(u_id)
    u.password = new_password
    db.session.commit()

def check_email(email):
    return UserAccount.query.filter(UserAccount.email.__eq__(email)).first()

def get_user_by_id(uid):
    return UserAccount.query.get(uid)

def get_registration_by_id(r_id):
    return Registration.query.get(r_id)

def get_user_by_username(username):
    return UserAccount.query.filter(UserAccount.username == username).first()

def get_user_by_email(email):
    return UserAccount.query.filter(UserAccount.email == email).first()

# def load_user_roles():
#     return [role for role in UserRole if role != UserRole.ADMIN]

def load_courses():
    return Course.query.all()

def load_levels():
    return Level.query.all()

def stats_revenue_by_month():
    return (db.session.query(db.func.sum(Transaction.money), db.func.date_format(Transaction.date, '%m')).
     group_by(db.func.date_format(Transaction.date, '%m'))).order_by(db.func.date_format(Transaction.date, '%m')).all()

def get_unpaid_registrations(kw=None):
    # 1. Lọc các trạng thái chưa hoàn thành
    query = Registration.query.filter(Registration.status != StatusTuition.PAID)
    if kw:
        query = query.join(UserAccount).filter(or_(
            UserAccount.name.contains(kw),
            UserAccount.phone_num.contains(kw),
            UserAccount.email.contains(kw)
        ))

    return query.all()

if __name__=="__main__":
    with app.app_context():
        print(auth_user("user", "123"))
        #print(load_user_roles())