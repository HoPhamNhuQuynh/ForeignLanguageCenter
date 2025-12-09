from datetime import datetime

from flask import redirect, request, flash, url_for
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func, or_, extract

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

# --- View Quy định ---
class RegulationView(AdminBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        # 1. Lấy dữ liệu cho Dropdown
        courses = Course.query.all()
        selected_course_id = request.args.get('course_id')

        # 2. Logic lọc Level theo Khóa học
        level_query = Level.query
        if selected_course_id and selected_course_id != 'all':
            level_query = level_query.join(Classroom).filter(Classroom.course_id == selected_course_id)

        levels = level_query.distinct().all()
        max_stu = 25

        # 3. Xử lý Lưu (POST)
        if request.method == 'POST':
            try:
                # Lưu sỉ số
                # new_max_stu = request.form.get('max_stu')

                # Lưu học phí
                for level in levels:
                    new_tuition = request.form.get(f'tuition_{level.id}')
                    if new_tuition:
                        level.tuition = float(new_tuition)

                db.session.commit()
                flash('Đã lưu quy định thành công.', 'success')
                return redirect(url_for('regulation.index', course_id=selected_course_id))
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {str(e)}', 'danger')

        return self.render('admin/regulation.html',
                           levels=levels,
                           courses=courses,
                           selected_course_id=selected_course_id,
                           max_stu=max_stu)


# 1. LẬP HÓA ĐƠN
class CreateInvoiceView(CashierView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        search_kw = request.args.get('search')
        unpaid_regis = dao.get_unpaid_registrations(search_kw)

        # Lấy ngày hôm nay để truyền sang HTML (làm giá trị mặc định cho ô input)
        today_str = datetime.now().strftime('%Y-%m-%d')

        student_info = None
        if search_kw and unpaid_regis:
            student_info = unpaid_regis[0].student

        if request.method == 'POST':
            try:
                regis_id = request.form.get('regis_id')
                amount = float(request.form.get('amount'))
                method = request.form.get('method')

                # --- [SỬA ĐOẠN NÀY ĐƠN GIẢN HƠN] ---
                date_input = request.form.get('created_date')  # Lấy chuỗi ngày yyyy-mm-dd

                if date_input:
                    # Chỉ cần ngày, giờ sẽ tự lấy là 00:00:00 hoặc bạn có thể ghép giờ hiện tại vào nếu muốn
                    created_date = datetime.strptime(date_input, '%Y-%m-%d')
                else:
                    created_date = datetime.now()
                # -----------------------------------

                regis = Registration.query.get(regis_id)
                if regis:
                    new_trans = Transaction(
                        money=amount,
                        content=f"Thu học phí: {regis.classroom.course.name}",
                        method=MethodEnum[method] if method else MethodEnum.CASH,
                        date=created_date,  # Lưu ngày
                        status=StatusPayment.SUCCESS,
                        regis_id=regis.id,
                        employee_id=current_user.id
                    )
                    db.session.add(new_trans)

                    regis.paid += amount
                    if regis.paid >= regis.actual_tuition:
                        regis.status = StatusTuition.PAID
                    else:
                        regis.status = StatusTuition.PARTIAL

                    db.session.commit()
                    flash('Thanh toán thành công!', 'success')
                    return redirect(url_for('invoice.index'))

            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi: {str(e)}', 'danger')

        # Truyền biến today_str sang HTML
        return self.render('admin/invoice_create.html',
                           student=student_info,
                           registrations=unpaid_regis,
                           today_str=today_str)

# 2. QUẢN LÝ HÓA ĐƠN
class InvoiceManagementView(CashierView):  # Hoặc CashierBaseView tùy code bạn đang dùng
    @expose('/')
    def index(self):
        # Lấy tham số từ URL
        kw = request.args.get('kw')
        status = request.args.get('status')  # Lấy giá trị ô chọn trạng thái

        # Gọi DAO với cả 2 tham số
        transactions = dao.get_transactions(kw, status)

        return self.render('admin/invoice_list.html', transactions=transactions)


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

                # --- 1. CÁC CHỈ SỐ CƠ BẢN (Giữ nguyên) ---
                stu_count = Student.query.count()
                total_revenue = db.session.query(func.sum(Transaction.money)).scalar() or 0
                pass_count = Score.query.filter(Score.value >= 5.0).count()
                total_scores = Score.query.count()
                pass_rate = round((pass_count / total_scores * 100), 1) if total_scores > 0 else 0

                # --- 2. DỮ LIỆU BIỂU ĐỒ 1: DOANH THU THEO THÁNG (Năm nay) ---
                current_year = datetime.now().year
                revenue_query = db.session.query(
                    extract('month', Transaction.date),
                    func.sum(Transaction.money)
                ).filter(extract('year', Transaction.date) == current_year) \
                    .group_by(extract('month', Transaction.date)) \
                    .all()

                # Tạo mảng 12 tháng, mặc định doanh thu là 0
                revenue_data = [0] * 12
                for month, money in revenue_query:
                    revenue_data[int(month) - 1] = money  # Gán doanh thu vào đúng tháng (index 0 = tháng 1)

                # --- 3. DỮ LIỆU BIỂU ĐỒ 2: SỐ LƯỢNG HỌC VIÊN THEO KHÓA HỌC ---
                # Join: Course -> Classroom -> Registration
                course_stats = db.session.query(
                    Course.name,
                    func.count(Registration.id)
                ).join(Classroom, Classroom.course_id == Course.id) \
                    .join(Registration, Registration.class_id == Classroom.id) \
                    .group_by(Course.id).all()

                # Tách thành 2 list riêng để ném vào ChartJS
                course_labels = [c[0] for c in course_stats]
                course_values = [c[1] for c in course_stats]

                return self.render('admin/report.html',
                                   stu_count=stu_count,
                                   total_revenue=total_revenue,
                                   pass_rate=pass_rate,
                                   # Truyền dữ liệu biểu đồ sang
                                   revenue_data=revenue_data,
                                   course_labels=course_labels,
                                   course_values=course_values)

            elif current_user.role == UserRole.CASHIER:
                return redirect(url_for('invoice.index'))
            else:
                logout_user()
                return redirect('/admin')

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
# 1. Lập hóa đơn
admin.add_view(CreateInvoiceView(name='Lập hóa đơn', endpoint='invoice'))

# 2. Quản lý hóa đơn (SỬA DÒNG NÀY)
# Thay TransactionHistoryView bằng InvoiceManagementView để hiện giao diện màu cam
admin.add_view(InvoiceManagementView(name='Quản lí hóa đơn', endpoint='management'))

# --- Menu chung ---
admin.add_view(MyLogoutView(name='Đăng xuất'))

if __name__ == '__main__':
    app.run(debug=True)