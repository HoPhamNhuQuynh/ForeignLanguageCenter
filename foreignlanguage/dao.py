import math

from flask_login import current_user
from sqlalchemy import or_, extract, func, not_
from sqlalchemy.orm import joinedload
from datetime import datetime
from foreignlanguage.models import (StudentInfo, UserAccount, Course, Transaction, Registration, StatusTuition, Level,
                                    Classroom, EmployeeInfo, MethodEnum, StatusPayment, CourseLevel, Session, Present,
                                    UserRole, AcademicStatus, Score, GradeCategory)
from foreignlanguage import app, db
import hashlib


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


def update_user_information_by_uid(uid, name, email, address, phone_num):
    u = get_user_by_id(uid)
    u.name = name
    u.email = email
    u.address = address
    u.phone_num = phone_num
    db.session.commit()


def update_user_avatar_by_uid(uid, avatar):
    u = get_user_by_id(uid)
    u.avatar = avatar
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


def load_teachers():
    return UserAccount.query.filter(UserAccount.role == UserRole.TEACHER).all()


def get_registration_by_id(r_id):
    return Registration.query.get(r_id)


def get_course_by_id(c_id):
    return Course.query.get(c_id)


def get_level_by_id(l_id):
    return Level.query.get(l_id)


def get_all_course_levels():
    return CourseLevel.query.options(
        joinedload(CourseLevel.course),
        joinedload(CourseLevel.level)
    ).order_by(CourseLevel.course_id, CourseLevel.level_id).all()


def get_tuition_by_course_level(c_id, l_id):
    return CourseLevel.query.filter(CourseLevel.course_id == c_id, CourseLevel.level_id == l_id).first()


def get_levels_by_course(course_id):
    return db.session.query(Level).join(CourseLevel, CourseLevel.level_id == Level.id).filter(
        CourseLevel.course_id == course_id).all()


# ====================== STUDENT ==========================
def create_registration(user, class_id, name, phone):
    classroom = get_class_by_id(class_id)
    tuition_base = classroom.course_level.tuition
    reg = db.session.query(Registration).filter(Registration.class_id == class_id,
                                                Registration.student_id == user.id,
                                                Registration.active == True).first()

    if not reg:
        reg = Registration(student_id=user.id, class_id=class_id, actual_tuition=tuition_base)
        db.session.add(reg)

    current_user.name = name
    current_user.phone_num = phone
    db.session.commit()
    return reg


def create_transaction(money, method, regis_id, **kwargs):
    transact = Transaction(
        money=money,
        method=method,
        regis_id=regis_id,
        **kwargs
    )
    db.session.add(transact)
    db.session.flush()
    return transact


def process_payment(transaction, result_payment, status_fee):
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
    # kt
    if amount != expected_money:
        return False

    reg = create_registration(user=user, class_id=class_id, name=name, phone=phone)
    transact = create_transaction(
        money=expected_money,
        method=method,
        regis_id=reg.id
    )
    result_payment = True
    return process_payment(transact, result_payment, status)


def register_and_pay_by_cashier(regis_id, amount, content, method, employee_id):
    regis = Registration.query.get(regis_id)
    if not regis:
        return False, "Không tìm thấy đăng ký"

    try:
        payment_method = MethodEnum(int(method))
    except (ValueError, KeyError):
        return False, f"Phương thức thanh toán '{method}' không hợp lệ"

    transact = create_transaction(
        money=amount,
        method=payment_method,
        regis_id=regis.id,
        content=content,
        status=StatusPayment.PENDING,
        employee_id=employee_id
    )
    db.session.add(transact)
    db.session.flush()

    status = (
        StatusTuition.PAID
        if regis.paid + amount >= regis.actual_tuition
        else StatusTuition.PARTIAL
    )
    success = process_payment(transact, True, status)
    return success, "Thanh toán thành công" if success else "Thanh toán thất bại"


def get_classes_by_course_level(c_id, l_id, student_id):
    query = (
        db.session.query(
            Classroom.id,
            Classroom.start_time,
            Classroom.maximum_stu,
            func.count(Registration.id).label('current_count')
        )
        .outerjoin(Registration, Classroom.id == Registration.class_id)
        .filter(
            Classroom.course_id == c_id,
            Classroom.level_id == l_id,
            Classroom.start_time >= datetime.now()
        )
        .group_by(Classroom.id)
        .having(func.count(Registration.id) < Classroom.maximum_stu)
    )

    if student_id:
        subquery = (
            db.session.query(Registration.class_id)
            .filter(Registration.student_id == student_id)
            .scalar_subquery()
        )
        query = query.filter(not_(Classroom.id.in_(subquery)))

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


def get_classes_by_student_id(student_id):
    results = db.session.query(
        Course.name.label('course_name'),
        Level.name.label('level_name'),
        Classroom.id.label('class_id'),
        Classroom.start_time.label('start_time'),
        UserAccount.name.label('teacher_name')
    ).join(Course, Course.id == Classroom.course_id) \
        .join(Level, Level.id == Classroom.level_id) \
        .join(Registration, Classroom.id == Registration.class_id) \
        .join(EmployeeInfo, Classroom.employee_id == EmployeeInfo.id) \
        .join(UserAccount, UserAccount.id == EmployeeInfo.u_id) \
        .filter(Registration.student_id == student_id).all()
    return results


# ==================== TEACHER ====================
def get_emloyee_by_user_id(user_id):
    return EmployeeInfo.query.filter_by(u_id=user_id).first()


def get_teacher_classes(employee_id):
    if not employee_id:
        return []
    return Classroom.query.filter_by(employee_id=employee_id).all()


def get_active_grade_categories():
    return GradeCategory.query.filter_by(active=1).all()


def get_sessions_by_class(class_id):
    return Session.query.filter_by(class_id=class_id).all()


def get_classroom_by_teacher(class_id, employee_id):
    return Classroom.query.filter_by(id=class_id, employee_id=employee_id).first()


def get_regs_by_class(class_id):
    return Registration.query.filter_by(class_id=class_id).all()


def get_present_by_session(session_id):
    return Present.query.filter_by(session_id=session_id).all()


def get_score_by_registration(reg_id, cate_id):
    return Score.query.filter_by(regis_id=reg_id, grade_cate_id=cate_id).first()


def update_final_score(reg_id):
    scores = Score.query.filter_by(regis_id=reg_id).all()

    if not scores:
        return

    total_weighted_score = 0
    total_weight = 0

    for s in scores:
        weight = s.grade_category.weight
        if s.value is not None:
            total_weighted_score += s.value * weight
            total_weight += weight

    if total_weight > 0:
        final_score = total_weighted_score / total_weight

        reg = Registration.query.get(reg_id)
        if reg:
            reg.final_score = round(final_score, 2)
            reg.academic_status = "PASSED" if final_score >= 5 else "FAILED"
            db.session.commit()


def save_present(session_id, student_status):
    try:
        for student_id, status in student_status.items():
            is_present = True if int(status) == 1 else False

            present = Present.query.get((int(session_id), int(student_id)))

            if present:
                present.is_present = is_present
            else:
                present = Present(
                    session_id=int(session_id),
                    student_id=int(student_id),
                    is_present=is_present
                )
                db.session.add(present)

        db.session.commit()
        return True

    except Exception as e:
        print(f"Lỗi khi cập nhật dữ liệu: {e}")
        db.session.rollback()
        return False


######### ADMIN ##############

def stats_revenue_per_month_by_year(year=None):
    query = ((db.session.query(
        func.sum(Transaction.money),
        extract('month', Transaction.joined_date)
    ).
              filter(extract('year', Transaction.joined_date) == year).
              group_by(extract('month', Transaction.joined_date))).
             order_by(extract('month', Transaction.joined_date)))
    return query.all()


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
             group_by(Course.id).all())
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
    query = db.session.query(func.count(UserAccount.id))
    query = query.filter(UserAccount.role == UserRole.STUDENT, extract('year', StudentInfo.joined_date) == year)
    return query.join(StudentInfo, StudentInfo.u_id == UserAccount.id).join(Registration,
                                                                            StudentInfo.id == Registration.student_id).scalar()


def count_active_classes(year=None):
    return Classroom.query.filter(extract('year', Classroom.start_time) == year, Classroom.active == 1).count()


def count_total_revenue(year=None):
    return db.session.query(func.sum(Transaction.money)).filter(extract('year', Transaction.joined_date) == year,
                                                                Transaction.status == StatusPayment.SUCCESS).scalar()


def stats_top3_popular_courses_by_year(year=None):
    return (db.session.query(
        Course.name,
        func.count(Registration.id)
    )
            .join(Classroom, Classroom.course_id == Course.id)
            .join(Registration, Registration.class_id == Classroom.id)
            .filter(extract('year', Classroom.start_time) == year)
            .group_by(Course.id)
            .order_by(func.count(Registration.id).desc())
            .limit(3)
            .all()
            )


def get_top3_courses_chart_data(year):
    top3_data = stats_top3_popular_courses_by_year(year)

    if not top3_data:
        return {"labels": [], "data": []}

    return {
        "labels": [name for name, count in top3_data],
        "data": [count for name, count in top3_data]
    }


def get_details_top3_courses(year=None):
    year = year if year else datetime.now().year
    return (
        db.session.query(
            Course,
            func.count(Registration.id)
        )
        .join(Classroom, Classroom.course_id == Course.id)
        .join(Registration, Registration.class_id == Classroom.id)
        .filter(extract('year', Classroom.start_time) == year)
        .group_by(Course.id)
        .order_by(func.count(Registration.id).desc())
        .limit(3)
        .all()
    )


def update_course_level_tuition(course_id, level_id, new_fee):
    config = CourseLevel.query.get((course_id, level_id))
    if config:
        config.tuition = float(new_fee)
        db.session.add(config)
        db.session.commit()


######### CASHIER #############
def get_unpaid_registrations(kw=None):
    query = Registration.query.filter(
        or_(
            Registration.status == StatusTuition.PARTIAL,
            Registration.status == StatusTuition.PENDING
        )
    )
    if kw:
        query = query.join(StudentInfo).join(UserAccount).filter(or_(
            UserAccount.name.contains(kw),
            UserAccount.phone_num.contains(kw),
            UserAccount.email.contains(kw)
        ))

    return query.all()


def delete_registration(reg_id):
    reg = Registration.query.get(reg_id)
    if reg:
        for trans in reg.transactions:
            trans.status = StatusPayment.FAILED

        reg.status = StatusTuition.FAILED
        reg.academic_status = AcademicStatus.FAILED
        reg.active = False
        db.session.commit()
        return True
    return False


def revert_payment(registration, money_to_revert):
    if not registration:
        return
    registration.paid -= money_to_revert
    if registration.paid < 0:
        registration.paid = 0
    if registration.paid == 0:
        delete_registration(registration.id)
        return
    if (registration.actual_tuition / 2).__eq__(registration.paid):
        registration.status = StatusTuition.PARTIAL
    db.session.add(registration)


### Cashier thêm
def load_students():
    return UserAccount.query.filter(UserAccount.role == UserRole.STUDENT).all()


def create_manual_invoice(student_id, class_id, amount, method, content, employee_id):
    classroom = Classroom.query.get(class_id)
    student_info = StudentInfo.query.get(student_id)

    if not student_info:
        return False, "Không tìm thấy thông tin học viên"

    if not classroom:
        return False, "Lớp học không tồn tại"

    tuition = classroom.course_level.tuition

    exist_reg = Registration.query.filter_by(
        student_id=student_id,
        class_id=class_id
    ).first()

    if exist_reg:
        return False, "Học viên đã đăng ký lớp này rồi!"

    new_reg = Registration(
        student_id=student_info.id,
        class_id=class_id,
        actual_tuition=tuition
    )
    db.session.add(new_reg)
    db.session.flush()

    return register_and_pay_by_cashier(
        regis_id=new_reg.id,
        amount=amount,
        content=content,
        method=method,
        employee_id=employee_id
    )


if __name__ == "__main__":
    with app.app_context():
        # print(auth_user("user", "123"))
        # print(get_classes_by_course_level(2, 2))
        # print(count_students(2024))
        # print(count_courses(2025))
        # print(count_active_classes(2025))
        # print(count_total_revenue(2024))
        # print(stats_rate_passed_per_course_by_year(2024))
        # print(get_tuition_by_class_id(22))
        # print(get_details_top3_courses())
        # top3 = get_details_top3_courses(2025)
        # course, total = top3[0]
        # print(course.id, course.name, course.description)
        print(get_classes_by_course_level(1, 2, 1))
