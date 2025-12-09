from flask import redirect, request, flash, url_for
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func, or_

from foreignlanguage import app, db, login
from foreignlanguage.models import (
    Student, Course, Classroom, Employee,
    Registration, Transaction, Score, UserRole, Level,
    StatusTuition, StatusPayment, MethodEnum
)
import dao

# =========================================================
# 1. CÁC CLASS CƠ CHẾ PHÂN QUYỀN
# =========================================================

class AdminView(ModelView):
    """Dùng cho các bảng chỉ Admin mới thấy"""
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class AdminBaseView(BaseView):
    """Dùng cho các trang custom (như Regulation) của Admin"""
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class CashierView(BaseView):
    """Dùng cho các trang custom của Cashier"""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.CASHIER


class CashierModelView(ModelView):
    """Dùng cho các bảng Cashier quản lý"""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.CASHIER


# =========================================================
# 2. CÁC VIEW CHỨC NĂNG
# =========================================================

# --- View Logout ---
class MyLogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


# --- View Quy định (Admin) ---
class RegulationView(AdminBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        levels = Level.query.all()
        # Mặc định max_stu, nếu bạn có lưu trong DB thì query ra, ko thì để cứng
        max_stu = 25

        if request.method == 'POST':
            try:
                for level in levels:
                    new_tuition = request.form.get(f'tuition_{level.id}')
                    if new_tuition:
                        level.tuition = float(new_tuition)
                db.session.commit()
                flash('Cập nhật quy định thành công!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {str(e)}', 'error')

        return self.render('admin/regulation.html', levels=levels, max_stu=max_stu)


# --- View Lập hóa đơn (Cashier) ---
class CreateInvoiceView(CashierView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        search_kw = request.args.get('search')
        student_info = None
        unpaid_regis = []

        # Logic tìm kiếm học viên
        if search_kw:
            search_kw = search_kw.strip()
            student_info = Student.query.filter(or_(
                Student.name.contains(search_kw),
                Student.phone_num.contains(search_kw)
            )).first()

            if student_info:
                unpaid_regis = Registration.query.filter(
                    Registration.student_id == student_info.id,
                    Registration.status != StatusTuition.PAID
                ).all()

        # Logic thanh toán (POST)
        if request.method == 'POST':
            try:
                regis_id = request.form.get('regis_id')
                amount = float(request.form.get('amount'))
                regis = Registration.query.get(regis_id)

                if regis:
                    new_trans = Transaction(
                        money=amount,
                        content=f"Thu học phí {regis.classroom.course.name}",
                        method=MethodEnum.CASH,
                        status=StatusPayment.SUCCESS,
                        regis_id=regis.id,
                        employee_id=current_user.id
                    )
                    db.session.add(new_trans)

                    # Cập nhật số tiền đã đóng
                    regis.paid += amount
                    if regis.paid >= regis.actual_tuition:
                        regis.status = StatusTuition.PAID
                    else:
                        regis.status = StatusTuition.PARTIAL

                    db.session.commit()
                    flash('Thanh toán thành công!', 'success')
                    return redirect(url_for('invoice.index', search=student_info.phone_num))
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi thanh toán: {str(e)}', 'error')

        return self.render('admin/invoice_create.html', student=student_info, registrations=unpaid_regis)


# --- View Lịch sử giao dịch (Cashier) ---
class TransactionHistoryView(CashierModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_list = ('id', 'date', 'student_name', 'content', 'money', 'method', 'status')
    column_labels = dict(id='Mã', date='Ngày', student_name='Học viên', content='Nội dung', money='Số tiền',
                         method='PTTT', status='Trạng thái')

    # Format hiển thị tên học viên từ relationship
    def _student_formatter(view, context, model, name):
        if model.registration and model.registration.student:
            return model.registration.student.name
        return "N/A"

    column_formatters = {'student_name': _student_formatter}


# =========================================================
# 3. ADMIN INDEX VIEW (XỬ LÝ LOGIN)
# =========================================================

class MyAdminIndexView(AdminIndexView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        # 1. Xử lý Login Form submit
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = dao.auth_user(username, password)
            if user:
                login_user(user)
                # Đăng nhập xong redirect về chính trang admin để nạp menu đúng quyền
                return redirect('/admin')
            else:
                flash('Sai tên đăng nhập hoặc mật khẩu!', 'danger')

        # 2. Điều hướng nếu đã đăng nhập
        if current_user.is_authenticated:
            if current_user.role == UserRole.ADMIN:
                # Nếu là Admin -> Hiện thống kê (Report)
                stu_count = Student.query.count()
                revenue = db.session.query(func.sum(Transaction.money)).scalar() or 0
                return self.render('admin/report.html', stu_count=stu_count, total_revenue=revenue)

            elif current_user.role == UserRole.CASHIER:
                # Nếu là Cashier -> Chuyển ngay sang trang Lập hóa đơn
                return redirect(url_for('invoice.index'))

            else:
                # Role khác không được vào
                logout_user()
                return redirect('/admin')

        # 3. Chưa đăng nhập -> Hiện Form Login
        return self.render('admin/index.html')

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

# =========================================================
# 4. KHỞI TẠO ADMIN & ADD VIEW
# =========================================================

admin = Admin(app=app, name='ANQUINKO', theme=Bootstrap4Theme(), index_view=MyAdminIndexView())

# --- Menu cho ADMIN ---
admin.add_view(AdminView(Course, db.session, name='Khóa học', category='Đào tạo'))
admin.add_view(AdminView(Classroom, db.session, name='Lớp học', category='Đào tạo'))
admin.add_view(AdminView(Employee, db.session, name='Nhân viên', category='Nhân sự'))
admin.add_view(AdminView(Student, db.session, name='Học viên', category='Nhân sự'))
admin.add_view(RegulationView(name='Quy định', endpoint='regulation'))

# --- Menu cho CASHIER ---
admin.add_view(CreateInvoiceView(name='Lập hóa đơn', endpoint='invoice'))
admin.add_view(TransactionHistoryView(Transaction, db.session, name='Lịch sử giao dịch', endpoint='history'))

# --- Menu chung ---
admin.add_view(MyLogoutView(name='Đăng xuất'))