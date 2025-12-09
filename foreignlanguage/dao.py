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
    return Student.query.filter(Student.username == username).first()

# def load_user_roles():
#     return [role for role in UserRole if role != UserRole.ADMIN]

def load_courses():
    return Course.query.all()

def load_levels_by_course_id():
    pass

#################################
# --- HÀM MỚI: LẤY DANH SÁCH NỢ TỪ SQL ---
def get_unpaid_registrations(kw=None):
    # 1. Lọc các trạng thái chưa hoàn thành
    query = Registration.query.filter(Registration.status != StatusTuition.PAID)

    # 2. Nếu có từ khóa -> Join bảng Student để tìm kiếm
    if kw:
        query = query.join(Student).filter(or_(
            Student.name.contains(kw),
            Student.phone_num.contains(kw),
            Student.email.contains(kw)
        ))

    return query.all()


# --- HÀM MỚI: LẤY LỊCH SỬ GIAO DỊCH TỪ SQL ---
def get_transactions(kw=None, status_str=None):
    query = Transaction.query.order_by(desc(Transaction.date))

    # 1. Lọc theo từ khóa (Tên, SĐT, Mã HĐ)
    if kw:
        query = query.join(Registration).join(Student).filter(or_(
            Student.name.contains(kw),
            Student.phone_num.contains(kw),
            Transaction.id == kw
        ))

    # 2. Lọc theo trạng thái (NẾU CÓ CHỌN)
    if status_str:
        # Chuyển chuỗi 'SUCCESS'/'FAILED' thành Enum tương ứng
        try:
            status_enum = StatusPayment[status_str]
            query = query.filter(Transaction.status == status_enum)
        except KeyError:
            pass  # Nếu status gửi lên sai thì bỏ qua

    return query.all()

if __name__=="__main__":
    with app.app_context():
        print(auth_user("user", "123"))
        #print(load_user_roles())