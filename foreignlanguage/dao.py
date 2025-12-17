import math
from sqlalchemy import or_, extract, func
from sqlalchemy.orm import joinedload
from datetime import datetime

from sqlalchemy.sql.operators import isnot

from foreignlanguage.models import (UserAccount, Course, Transaction, Registration, StatusTuition, Level, StudentInfo,
                                    Classroom, EmployeeInfo, MethodEnum, StatusPayment, CourseLevel, Session, Present,
                                    UserRole, AcademicStatus)
from foreignlanguage import app, db
import hashlib
from flask_login import current_user


# ==================== AUTH & USER ====================
def auth_user(username, password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return UserAccount.query.filter(UserAccount.username.__eq__(username.strip()),
                                    UserAccount.password.__eq__(password)).first()


def add_user(username, password, email, address):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    u = UserAccount(username=username, password=password, email=email, address=address)
    db.session.add(u)
    db.session.commit()

def get_info_of_current_user_by_uid(u_id):
    return StudentInfo.query.filter(StudentInfo.u_id == u_id).first()

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


def get_course_by_id(c_id):
    return Course.query.get(c_id)


def get_level_by_id(l_id):
    return Level.query.get(l_id)


# ====================== STUDENT ==========================
def create_registration(user, class_id, name, phone):
    classroom = get_class_by_id(class_id)
    tuition_base = classroom.course_level.tuition
    reg = db.session.query(Registration).filter(Registration.class_id == class_id,
                                                        Registration.student_id == user.id,
                                                         Registration.active == True).first()

    if not reg:
        reg = Registration(student_id=user.id, class_id=class_id, actual_tuition= tuition_base)
        db.session.add(reg)

    user.name = name
    user.phone_num = phone
    db.session.commit()
    return reg


def create_transaction(money, method, regis_id):
    transact = Transaction(money=money, method=method, regis_id=regis_id)
    db.session.add(transact)
    db.session.flush()

    return transact

def process_payments(transaction, result_payment, status_fee): # cua Quynh viet nha
    result_payment = True
    if result_payment:
        transaction.status = StatusPayment.SUCCESS
        transaction.registration.paid += transaction.money
        transaction.registration.status = status_fee
        db.session.commit()
        return True
    else:
        transaction.status = StatusPayment.FAILED
        db.session.commit()
        return False

def register_and_pay(user, class_id, amount, method, payment_percent, name, phone):
    classroom = get_class_by_id(class_id)
    tuition_base = classroom.course_level.tuition
    if payment_percent == 50:
        expected_money = math.ceil(tuition_base / 2)
        status = StatusTuition.PARTIAL
    else:
        expected_money = tuition_base
        status = StatusTuition.PAID

    if amount != expected_money:
        return

    reg = create_registration(user=user, class_id=class_id, name=name, phone=phone)
    transact = create_transaction(money=expected_money, method=method, regis_id=reg.id)
    process_result = True #gia lap cong thanh toan tra ve ket qua giao dich la thanh cong
    is_success = process_payments(transact, process_result, status)
    return is_success


def get_classes_by_course_level(c_id, l_id):
    query = db.session.query(
        Classroom.id,
        Classroom.start_time,
        Classroom.maximum_stu,
        func.count(Registration.student_id).label('current_count')
    ).outerjoin(
        Registration, Classroom.id == Registration.class_id
    ).filter(
        Classroom.course_id == c_id,
        Classroom.level_id == l_id,
        Classroom.start_time.__ge__(datetime.now())
    ).group_by(
        Classroom.id, Classroom.start_time, Classroom.maximum_stu
    ).having(
        func.count(Registration.student_id) < Classroom.maximum_stu
    )
    return query.all()


def get_payment_methods():
    return [
        {
            "name": method.name,
            "value": method.value
        }
        for method in MethodEnum
        if method != MethodEnum.CASH
    ]


def get_class_by_id(class_id):
    return Classroom.query.get(class_id)


def get_tuition_by_class_id(class_id):
    row = (
        db.session.query(CourseLevel.tuition)
        .join(Classroom.course_level)
        .filter(Classroom.id == class_id)
        .first()
    )
    return float(row[0]) if row else 0
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


def get_teacher_classes(user_id):
    employee = EmployeeInfo.query.filter_by(u_id=user_id).first()
    if not employee:
        return []
    return Classroom.query.filter_by(employee_id=employee.id).all()


def get_rollcall_data(user_id, class_id):
    employee = EmployeeInfo.query.filter_by(u_id=user_id).first()
    if not employee:
        return None, None

    classroom = Classroom.query.filter_by(
        id=class_id,
        employee_id=employee.id
    ).first()

    if not classroom:
        return None, None

    sessions = Session.query.filter_by(class_id=class_id).all()

    regs = Registration.query.filter_by(class_id=class_id).all()
    students = [r.student for r in regs]

    return sessions, students


def save_attendance(session_id: int, student_status: dict):
    for stu_id, status in student_status.items():
        is_present = status == "1"
        present = Present.query.filter_by(session_id=session_id, student_id=stu_id).first()
        if present:
            present.is_present = is_present
        else:
            db.session.add(Present(session_id=session_id, student_id=stu_id, is_present=is_present))
    db.session.commit()


######### ADMIN ##############
def stats_revenue_per_month_by_year(year=None):
    query = ((db.session.query(
        func.sum(Transaction.money),
        extract('month', Transaction.date)
    ).
              filter(extract('year', Transaction.date) == year).
              group_by(extract('month', Transaction.date))).
             order_by(extract('month', Transaction.date)).
             all())
    return query


def get_revenue_chart_data(year):
    revenue_date = stats_revenue_per_month_by_year(year)

    if not revenue_date:
        return {"labels": [], "data": []}

    return {
        "labels": [date for amount, date in revenue_date],
        "data": [amount for amount, date in revenue_date]
    }


def stats_rate_passed_per_course_by_year(year=None):
    query = db.session.query(func.count(Registration.id), Course.name). \
        join(Classroom, Classroom.id == Registration.class_id). \
        join(Course, Course.id == Classroom.course_id). \
        filter(extract('year', Classroom.start_time) == year, Registration.academic_status == AcademicStatus.PASSED). \
        group_by(Course.id)
    return query.all()


def get_ratio_passed_chart_data(year):
    ratio_passed_data = stats_rate_passed_per_course_by_year(year)
    total_achieved = sum(amount for amount, name in ratio_passed_data)

    if not ratio_passed_data:
        return {"labels": [], "data": []}

    return {
        "labels": [name for amount, name in ratio_passed_data],
        "data": [amount / total_achieved * 100 for amount, name in ratio_passed_data]
    }


def stats_numbers_of_students_per_course_by_year(year=None):
    query = (db.session.query(
        func.count(Registration.student_id),
        Course.name
    ).
             join(Classroom, Course.id == Classroom.course_id).
             join(Registration, Registration.class_id == Classroom.id).
             filter(extract('year', Classroom.start_time) == year).
             group_by(Course.name).all())
    return query


def get_student_chart_data(year):
    student_data = stats_numbers_of_students_per_course_by_year(year)

    if not student_data:
        return {"labels": [], "data": []}

    return {
        "labels": [name for amount, name in student_data],
        "data": [amount for amount, name in student_data]
    }


def count_courses(year=None):
    return Course.query.filter(extract('year', Course.joined_date) == year).count()


def count_students(year=None):
    return db.session.query(func.count(UserAccount.id)).filter(UserAccount.role == UserRole.STUDENT,
                                                               UserAccount.name.isnot(None),
                                                               extract('year', UserAccount.joined_date) == year).scalar()


def count_active_classes(year=None):
    return Classroom.query.filter(Classroom.active == 1).filter(extract('year', Classroom.joined_date) == year).count()


def count_total_revenue(year=None):
    return db.session.query(func.sum(Transaction.money)).filter(extract('year', Transaction.date) == year, Transaction.status==StatusPayment.SUCCESS).scalar()


def stats_top3_popular_courses_by_year(year=None):
    query = (
        db.session.query(
            Course.name,
            func.count(Registration.id)  # số học viên đăng ký
        )
        .join(Classroom, Classroom.course_id == Course.id)
        .join(Registration, Registration.class_id == Classroom.id)
        .filter(extract('year', Classroom.start_time) == year)
        .group_by(Course.id)
        .order_by(func.count(Registration.id).desc())
        .limit(3)
        .all()
    )
    return query


def get_top3_courses_chart_data(year):
    top3_data = stats_top3_popular_courses_by_year(year)

    if not top3_data:
        return {"labels": [], "data": []}

    return {
        "labels": [name for name, count in top3_data],
        "data": [count for name, count in top3_data]
    }


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

def get_all_course_levels():
    """Lấy danh sách cấu hình học phí kèm thông tin Khóa và Level"""
    # Dùng joinedload để tối ưu query (nối bảng lấy tên)
    return CourseLevel.query.options(
        joinedload(CourseLevel.course),
        joinedload(CourseLevel.level)
    ).order_by(CourseLevel.course_id, CourseLevel.level_id).all()

def update_course_level_tuition(course_id, level_id, new_fee):
    """Cập nhật học phí dựa trên khóa chính tổ hợp (course_id, level_id)"""
    # SQLAlchemy hỗ trợ lấy composite PK bằng cách truyền tuple
    config = CourseLevel.query.get((course_id, level_id))
    if config:
        config.tuition = float(new_fee)
        db.session.add(config)

def save_changes():
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

if __name__ == "__main__":
    with app.app_context():
        # print(auth_user("user", "123"))
        print(get_classes_by_course_level(2, 2))
        print(count_students(2024))
        print(count_courses(2025))
        print(count_active_classes(2025))
        print(count_total_revenue(2025))
        print(stats_rate_passed_per_course_by_year(2025))
        print(get_tuition_by_class_id(22))
