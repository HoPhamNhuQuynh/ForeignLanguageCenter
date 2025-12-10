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

# 1. CÁC CLASS CƠ CHẾ PHÂN QUYỀN
class AdminView(ModelView):
    """Dùng cho các bảng chỉ Admin mới thấy"""
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN


class AdminBaseView(BaseView):
    """Dùng cho các trang custom """
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

# 2. CÁC VIEW CHỨC NĂNG

# --- View Logout ---
class MyLogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated

################Phần chức năng ADMIN####################
#Báo cáo Quỳnh sẽ làm ở đây!
class StatsView(AdminBaseView):
    # Chỉ Admin mới xem được báo cáo
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    @expose('/')
    def index(self):
        pass

# --- View Quy định học phí ---
class RegulationView(AdminBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        # 1. Lấy TẤT CẢ cấp độ (Không cần lọc theo khóa học nữa)
        levels = Level.query.all()

        # 2. Xử lý Lưu (POST)
        if request.method == 'POST':
            try:
                # Duyệt qua từng level để cập nhật học phí
                for level in levels:
                    # Lấy giá trị từ ô input có name="tuition_ID"
                    new_tuition = request.form.get(f'tuition_{level.id}')

                    if new_tuition:
                        level.tuition = float(new_tuition)

                # Commit thay đổi vào MySQL
                db.session.commit()
                flash('Đã cập nhật học phí thành công!', 'success')

                # Reload lại trang
                return redirect(url_for('regulation.index'))

            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi hệ thống: {str(e)}', 'danger')

        return self.render('admin/regulation.html', levels=levels)

############Chức năng của cashier##################
# LẬP HÓA ĐƠN
class CreateInvoiceView(CashierView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        search_kw = request.args.get('search')
        # Lấy danh sách những người chưa đóng xong tiền (UNPAID hoặc PARTIAL)
        unpaid_regis = dao.get_unpaid_registrations(search_kw)

        today_str = datetime.now().strftime('%Y-%m-%d')
        student_info = None

        # Nếu có tìm kiếm, lấy thông tin học viên đầu tiên để hiển thị lên form
        if search_kw and unpaid_regis:
            student_info = unpaid_regis[0].student

        if request.method == 'POST':
            try:
                # 1. Lấy dữ liệu từ Form
                regis_id = request.form.get('regis_id')
                amount = float(request.form.get('amount'))  # Số tiền đóng LẦN NÀY
                method = request.form.get('method')
                content = request.form.get('content')
                date_input = request.form.get('created_date')

                # Xử lý ngày tháng
                if date_input:
                    created_date = datetime.strptime(date_input, '%Y-%m-%d')
                else:
                    created_date = datetime.now()

                # 2. Lấy thông tin Registration từ DB để tính toán
                regis = Registration.query.get(regis_id)

                if regis:
                    # Tính số nợ HIỆN TẠI (trước khi đóng khoản này)
                    # Công thức: Tổng học phí - Tổng đã đóng các lần trước
                    current_debt = regis.actual_tuition - regis.paid

                    # --- VALIDATION (Kiểm tra dữ liệu) ---
                    if current_debt <= 0:
                        flash('Học viên này đã hoàn tất học phí rồi, không thể thu thêm!', 'danger')
                        return redirect(url_for('invoice.index'))

                    # Cho phép sai số nhỏ (1000đ) do làm tròn số thực
                    if amount > current_debt + 1000:
                        flash(f'Lỗi: Số tiền đóng ({amount:,.0f}đ) lớn hơn số nợ còn lại ({current_debt:,.0f}đ)!',
                              'danger')
                        return redirect(url_for('invoice.index', search=search_kw))

                    if amount <= 0:
                        flash('Số tiền đóng phải lớn hơn 0!', 'danger')
                        return redirect(url_for('invoice.index', search=search_kw))

                    # --- BƯỚC 1: TẠO GIAO DỊCH MỚI (Lưu lịch sử) ---
                    # Luôn là SUCCESS vì đây là thu tại quầy (Tiền trao cháo múc)
                    new_trans = Transaction(
                        money=amount,
                        content=content if content else f"Thu học phí đợt: {created_date.strftime('%d/%m')}",
                        method=MethodEnum[method] if method else MethodEnum.CASH,
                        date=created_date,
                        status=StatusPayment.SUCCESS,  # <-- Đặt SUCCESS luôn
                        regis_id=regis.id,
                        employee_id=current_user.id
                    )
                    db.session.add(new_trans)

                    # --- BƯỚC 2: CẬP NHẬT TRẠNG THÁI TỔNG (Registration) ---
                    # Cộng dồn số tiền vừa đóng vào tổng đã đóng
                    regis.paid = regis.paid + amount

                    # Tính lại nợ sau khi đóng xong khoản này
                    remaining_debt = regis.actual_tuition - regis.paid

                    # Cập nhật trạng thái dựa trên nợ còn lại
                    if remaining_debt <= 1000:  # Coi như hết nợ (dùng <= 1000 để tránh lỗi số lẻ 0.0001)
                        regis.status = StatusTuition.PAID
                        flash(f'Thu thành công {amount:,.0f}đ. Học viên đã HOÀN TẤT học phí!', 'success')
                    else:
                        regis.status = StatusTuition.PARTIAL
                        flash(f'Thu thành công {amount:,.0f}đ. Học viên còn nợ lại {remaining_debt:,.0f}đ.', 'warning')

                    db.session.commit()
                    return redirect(url_for('invoice.index'))

            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi hệ thống: {str(e)}', 'danger')

        return self.render('admin/invoice_create.html',
                           student=student_info,
                           registrations=unpaid_regis,
                           today_str=today_str)
#Quản lý hóa đơn
class TransactionAdminView(CashierModelView):
    # 1. CẤU HÌNH QUYỀN HẠN
    can_create = False
    can_edit = False
    can_delete = True
    can_export = True

    # 2. CẤU HÌNH HIỂN THỊ
    column_list = ('id', 'student_info', 'course_info', 'money', 'method', 'date', 'status', 'content')

    # Cấu hình danh sách cột khi xuất file (Export)
    export_types = ['csv']  # Chỉ định định dạng xuất (mặc định là CSV)

    column_labels = dict(
        id='Mã HĐ',
        student_info='Học viên',
        course_info='Khóa học',
        money='Số tiền',
        method='Hình thức',
        date='Ngày nộp',
        status='Trạng thái',
        content='Nội dung'
    )

    column_default_sort = ('date', True)

    # 3. TÌM KIẾM & BỘ LỌC
    column_searchable_list = ['id', 'content', 'registration.student.name', 'registration.student.phone_num']
    column_filters = ['status', 'method', 'date', 'money', 'registration.student.name']

    # 4. FORMAT DỮ LIỆU
    def _student_formatter(view, context, model, name):
        if model.registration and model.registration.student:
            return f"{model.registration.student.name} ({model.registration.student.phone_num})"
        return "N/A"

    def _course_formatter(view, context, model, name):
        if model.registration and model.registration.classroom:
            return model.registration.classroom.course.name
        return "N/A"

    def _money_formatter(view, context, model, name):
        return "{:,.0f} đ".format(model.money)

    column_formatters = {
        'student_info': _student_formatter,
        'course_info': _course_formatter,
        'money': _money_formatter
    }

    column_formatters_export = {
        'student_info': _student_formatter,
        'course_info': _course_formatter,
        'money': _money_formatter
    }
    def on_model_delete(self, model):
        if model.registration:
            # Bước 1: Trừ số tiền đã đóng trong hồ sơ gốc (Registration)
            # (Hoàn tác lại hành động đóng tiền)
            model.registration.paid -= model.money

            # Đảm bảo không bị âm (Safety check)
            if model.registration.paid < 0:
                model.registration.paid = 0

            # Bước 2: Cập nhật lại trạng thái nợ
            # Tính nợ sau khi xóa giao dịch
            debt = model.registration.actual_tuition - model.registration.paid

            if model.registration.paid == 0:
                # Nếu đã trả lại hết tiền đóng -> Về trạng thái CHƯA ĐÓNG
                model.registration.status = StatusTuition.UNPAID
            elif debt <= 0:
                # Vẫn còn thừa tiền (hiếm gặp) -> ĐÃ ĐÓNG
                model.registration.status = StatusTuition.PAID
            else:
                # Vẫn còn đóng 1 ít nhưng chưa đủ -> TRẢ GÓP (PARTIAL)
                model.registration.status = StatusTuition.PARTIAL

            # Lưu thay đổi của Registration vào session
            # (Flask-Admin sẽ tự động commit cùng lúc với việc xóa Transaction)
            db.session.add(model.registration)


############## XỬ LÝ LOGIN #####################

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
                # Login xong reload lại trang chủ
                return redirect('/admin')
            else:
                flash('Sai tên đăng nhập hoặc mật khẩu!', 'danger')

        # 2. NẾU ĐÃ ĐĂNG NHẬP -> HIỆN TRANG HOME CHUNG (home.html)
        if current_user.is_authenticated:
            # Không redirect đi đâu cả, ai cũng vào trang Home này
            return self.render('admin/home.html')

        # 3. Chưa đăng nhập -> Hiện Form Login
        return self.render('admin/index.html')

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

# 4. KHỞI TẠO ADMIN & ADD VIEW

admin = Admin(app=app, name='ANQUINKO', theme=Bootstrap4Theme(), index_view=MyAdminIndexView())

# --- Menu cho ADMIN ---
admin.add_view(StatsView(name='Thống kê báo cáo', endpoint='stats'))
admin.add_view(AdminView(Course, db.session, name='Khóa học', category='Đào tạo'))
admin.add_view(AdminView(Classroom, db.session, name='Lớp học', category='Đào tạo'))
admin.add_view(AdminView(Employee, db.session, name='Nhân viên', category='Người dùng'))
admin.add_view(AdminView(Student, db.session, name='Học viên', category='Người dùng'))
admin.add_view(RegulationView(name='Quy định', endpoint='regulation'))

# --- Menu cho CASHIER ---
admin.add_view(CreateInvoiceView(name='Lập hóa đơn', endpoint='invoice'))
admin.add_view(TransactionAdminView(Transaction, db.session, name='Quản lý giao dịch', endpoint='transaction'))

# --- Menu chung ---
admin.add_view(MyLogoutView(name='Đăng xuất'))

if __name__ == '__main__':
    app.run(debug=True)