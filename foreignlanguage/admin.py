from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func, or_
from foreignlanguage import app, db
from foreignlanguage.models import (
    Student, Course, Classroom, Employee,
    Registration, Transaction, Score, UserRole, Level,
    StatusTuition, StatusPayment, MethodEnum
)
import dao

# =========================================================
# 1. BASE VIEWS & PHÂN QUYỀN
# =========================================================

class AdminOnlyMixin:
    """Mixin kiểm tra quyền Admin"""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.index'))


class CashierOnlyMixin:
    """Mixin kiểm tra quyền Cashier"""

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.CASHIER

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.index'))


# Các class View thực tế kế thừa từ Mixin + View gốc
class AdminModelView(AdminOnlyMixin, ModelView):
    pass


class AdminBaseView(AdminOnlyMixin, BaseView):
    pass


class CashierBaseView(CashierOnlyMixin, BaseView):
    pass


class CashierModelView(CashierOnlyMixin, ModelView):
    pass

# =========================================================
# 2. TRANG CHỦ (INDEX) & XỬ LÝ LOGIN TẬP TRUNG
# =========================================================

class MyHomeScreen(AdminIndexView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        # --- XỬ LÝ ĐĂNG NHẬP (POST) ---
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = dao.auth_user(username, password)
            if user:
                login_user(user)
                return redirect(url_for('admin.index'))
            else:
                flash('Sai tên đăng nhập hoặc mật khẩu!', 'danger')

        # --- ĐIỀU HƯỚNG SAU KHI LOGIN (GET) ---
        if current_user.is_authenticated:
            # 1. Admin -> Xem Báo cáo
            if current_user.role == UserRole.ADMIN:
                stu_count = Student.query.count()
                revenue_data = db.session.query(func.sum(Transaction.money)).scalar() or 0
                pass_count = Score.query.filter(Score.value >= 5.0).count()
                total_scores = Score.query.count()
                pass_rate = round((pass_count / total_scores * 100), 1) if total_scores > 0 else 0

                return self.render('admin/report.html',
                                   stu_count=stu_count,
                                   total_revenue=revenue_data,
                                   pass_rate=pass_rate)

            # 2. Cashier -> Xem Lập hóa đơn
            if current_user.role == UserRole.CASHIER:
                return redirect(url_for('invoice.index'))

            # Role khác -> Logout
            logout_user()
            return redirect(url_for('admin.index'))

        # --- CHƯA LOGIN -> HIỆN FORM ---
        # Render file admin/index.html chứa form login
        return self.render('admin/index.html')


# =========================================================
# 3. CÁC CHỨC NĂNG CỤ THỂ
# =========================================================

# --- ADMIN: Thay đổi quy định ---
class RegulationView(AdminBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        levels = Level.query.all()
        default_max_stu = 25
        if request.method == 'POST':
            try:
                for level in levels:
                    new_tuition = request.form.get(f'tuition_{level.id}')
                    if new_tuition: level.tuition = float(new_tuition)
                # new_max_stu = request.form.get('max_stu') # Lưu setting nếu có bảng settings
                db.session.commit()
                flash('Cập nhật quy định thành công!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {str(e)}', 'error')
        return self.render('admin/regulation.html', levels=levels, max_stu=default_max_stu)


# --- CASHIER: Lập hóa đơn ---
class CreateInvoiceView(CashierBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        search_kw = request.args.get('search')
        unpaid_regis = []
        student_info = None

        if search_kw:
            search_kw = search_kw.strip()
            student = Student.query.filter(or_(
                Student.name.contains(search_kw),
                Student.phone_num.contains(search_kw)
            )).first()

            if student:
                student_info = student
                unpaid_regis = Registration.query.filter(
                    Registration.student_id == student.id,
                    Registration.status != StatusTuition.PAID
                ).all()

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
                    regis.paid += amount
                    regis.status = StatusTuition.PAID if regis.paid >= regis.actual_tuition else StatusTuition.PARTIAL
                    db.session.commit()
                    flash('Thanh toán thành công!', 'success')
                    return redirect(url_for('invoice.index', search=student.phone_num))
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {str(e)}', 'error')

        return self.render('admin/invoice_create.html', student=student_info, registrations=unpaid_regis)


# --- CASHIER: Lịch sử giao dịch ---
class TransactionView(CashierModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_list = ('id', 'date', 'student_name', 'content', 'money', 'method', 'status')
    column_labels = dict(id='Mã HD', date='Ngày thu', student_name='Học viên', content='Nội dung', money='Số tiền',
                         method='PTTT', status='Trạng thái')
    column_searchable_list = ['content']
    column_filters = ['status', 'method', 'date']

    def _student_formatter(view, context, model, name):
        return model.registration.student.name if model.registration and model.registration.student else "N/A"

    column_formatters = {'student_name': _student_formatter}


# --- CHUNG: Đăng xuất ---
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated


# =========================================================
# 4. KHỞI TẠO ADMIN & ADD VIEW
# =========================================================

admin = Admin(
    app=app,
    name='ANQUINKO',
    theme=Bootstrap4Theme(),
    index_view=MyHomeScreen(name='Trang chủ', url='/admin')
)

# --- MENU ADMIN (Có Category để gom nhóm) ---
admin.add_view(AdminModelView(Course, db.session, name='Khóa học', category='Quản lí khóa học'))
admin.add_view(AdminModelView(Classroom, db.session, name='Lớp học', category='Quản lí khóa học'))
admin.add_view(RegulationView(name='Thay đổi quy định', endpoint='regulation'))  # Không category -> Nằm ngang
admin.add_view(AdminModelView(Student, db.session, name='Học viên', category='Thông tin nhân sự'))
admin.add_view(AdminModelView(Employee, db.session, name='Nhân viên', category='Thông tin nhân sự'))

admin.add_view(CreateInvoiceView(name='Lập hóa đơn', endpoint='invoice'))
admin.add_view(TransactionView(Transaction, db.session, name='Lịch sử giao dịch', endpoint='history'))

# --- LOGOUT ---
admin.add_view(LogoutView(name='Đăng xuất'))

if __name__ == '__main__':
    app.run(debug=True)