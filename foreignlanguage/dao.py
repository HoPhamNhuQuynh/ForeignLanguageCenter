from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from foreignlanguage.models import UserAccount, Course, Transaction, Registration, StatusTuition, Level, StudentInfo, \
    Classroom, EmployeeInfo, MethodEnum, StatusPayment
from foreignlanguage import app, db
import hashlib

# ==================== AUTH & USER ====================
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

def get_user_by_username(username):
    return UserAccount.query.filter(UserAccount.username == username).first()

def get_user_by_email(email):
    return UserAccount.query.filter(UserAccount.email == email).first()

# ==================== COMMON LOADERS ====================
def load_courses():
    return Course.query.all()

def load_levels():
    return Level.query.all()

def get_registration_by_id(r_id):
    return Registration.query.get(r_id)

# ==================== TEACHER ====================
def get_course_by_teacher(user_id):
    return (db.session.query(Classroom)
            .join(EmployeeInfo, EmployeeInfo.id == Classroom.employee_id)
            .filter(EmployeeInfo.u_id == user_id).all())

def get_student_by_course(course_id):
    return (db.session.query(Registration)
            .join(StudentInfo, Registration.student_id == StudentInfo.id)
            .join(UserAccount, StudentInfo.u_id == UserAccount.id)
            .filter(Registration.class_id == course_id).all())

def get_scores_by_course(course_id):
    return (db.session.query(Registration)
        .join(StudentInfo, Registration.student_id == StudentInfo.id)
        .join(UserAccount, StudentInfo.u_id == UserAccount.id)
        .filter(Registration.class_id == course_id).all())

######### ADMIN ##############
def stats_revenue_by_month():
    return (db.session.query(db.func.sum(Transaction.money), db.func.date_format(Transaction.date, '%m')).
     group_by(db.func.date_format(Transaction.date, '%m'))).order_by(db.func.date_format(Transaction.date, '%m')).all()

######### CASHIER #############
def get_unpaid_registrations(kw=None):
    """Lấy danh sách học viên chưa hoàn thành học phí"""
    query = Registration.query.filter(Registration.status != StatusTuition.PAID)
    if kw:
        query = query.join(StudentInfo).join(UserAccount).filter(or_(
            UserAccount.name.contains(kw),
            UserAccount.phone_num.contains(kw),
            UserAccount.email.contains(kw)
        ))
    return query.all()

def update_tuition_fee(level_id, new_fee):
    """Cập nhật học phí cho 1 level"""
    level = Level.query.get(level_id)
    if level:
        level.tuition = float(new_fee)
        db.session.add(level)
        # Lưu ý: commit sẽ được gọi ở view hoặc gọi batch update

def save_changes():
    """Hàm wrapper để commit db"""
    db.session.commit()


def process_payment(regis_id, amount, content, method, created_date, employee_id):
    """
    Xử lý toàn bộ quy trình đóng tiền:
    1. Tạo Transaction
    2. Cộng tiền vào Registration
    3. Cập nhật trạng thái (PAID/PARTIAL)
    """
    regis = Registration.query.get(regis_id)
    if not regis: return False, "Không tìm thấy đăng ký"

    # 1. Tạo Transaction
    new_trans = Transaction(
        money=amount,
        content=content if content else f"Thu học phí đợt: {created_date.strftime('%d/%m')}",
        method=MethodEnum[method] if isinstance(method, str) else method,
        date=created_date,
        status=StatusPayment.SUCCESS,
        regis_id=regis.id,
        employee_id=employee_id
    )
    db.session.add(new_trans)

    # 2. Update Registration
    regis.paid += amount

    # 3. Update Status
    debt = regis.actual_tuition - regis.paid
    if debt <= 1000:
        regis.status = StatusTuition.PAID
        msg = "Đã hoàn tất học phí!"
    else:
        regis.status = StatusTuition.PARTIAL
        msg = f"Còn nợ {debt:,.0f}đ."

    db.session.add(regis)
    db.session.commit()
    return True, msg


# --- XỬ LÝ HOÀN TÁC KHI XÓA ---
def revert_payment(registration, money_to_revert):
    """
    Xử lý khi xóa giao dịch:
    1. Trừ tiền đã đóng trong Registration
    2. Cập nhật lại trạng thái
    """
    if not registration: return

    registration.paid -= money_to_revert
    if registration.paid < 0: registration.paid = 0

    debt = registration.actual_tuition - registration.paid

    if registration.paid == 0:
        registration.status = StatusTuition.UNPAID
    elif debt <= 1000:
        registration.status = StatusTuition.PAID
    else:
        registration.status = StatusTuition.PARTIAL

    db.session.add(registration)

def get_transaction_query_options(query):
    """Hàm tối ưu truy vấn Transaction để fix lỗi Export CSV"""
    return query.options(
        joinedload(Transaction.registration).joinedload(Registration.student).joinedload(StudentInfo.account),
        joinedload(Transaction.registration).joinedload(Registration.classroom).joinedload(Classroom.course)
    )
if __name__=="__main__":
    with app.app_context():
        print(auth_user("user", "123"))
        #print(load_user_roles())