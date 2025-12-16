from datetime import datetime
from flask import redirect, request, flash, url_for, jsonify
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user, login_user, logout_user
from flask_sqlalchemy.session import Session

from foreignlanguage import app, db, login
from foreignlanguage.models import (
    StudentInfo, Course, Classroom, EmployeeInfo,
    Registration, Transaction, UserRole, Score,
    Session, GradeCategory
)
import dao

class AuthenticationView(ModelView):
    def __init__(self, model, session, role=None, *args, **kwargs):
        self.required_role = role
        super().__init__(model, session, *args, **kwargs)
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.role==self.required_role

class AuthenticationBaseView(BaseView):
    def __init__(self, role=None, *args, **kwargs):
        self.required_role = role
        super().__init__(*args, **kwargs)
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.role == self.required_role

########### Khôi lỡ làm kiểu kế thừa roi ##############
# --- Dành cho ADMIN ---
class AdminView(AuthenticationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, role=UserRole.ADMIN, **kwargs)

class AdminBaseView(AuthenticationBaseView):
    def __init__(self, *args, **kwargs):
        super().__init__(role=UserRole.ADMIN, *args, **kwargs)

# --- Dành cho CASHIER (Thu ngân) ---
class CashierModelView(AuthenticationView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, role=UserRole.CASHIER, **kwargs)

class CashierView(AuthenticationBaseView):
    def __init__(self, *args, **kwargs):
        super().__init__(role=UserRole.CASHIER, *args, **kwargs)

# --- Dành cho TEACHER (Giáo viên) ---
class TeacherView(AuthenticationBaseView):
    def __init__(self, *args, **kwargs):
        super().__init__(role=UserRole.TEACHER, *args, **kwargs)

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
# --- Báo cáo Dashboard (Admin) ---
class StatsView(AdminBaseView):
    @expose('/')
    def index(self):
        year = request.args.get('year', type=int)
        if not year:
            year = datetime.now().year

        years = list(range(2024, datetime.now().year + 1))

        stats_students = dao.count_students(year)
        stars_courses = dao.count_courses(year)
        stats_classes = dao.count_active_classes(year)
        stats_total_revenue = dao.count_total_revenue(year)

        revenue_data = dao.get_revenue_chart_data(year)
        student_data = dao.get_student_chart_data(year)
        ratio_passed_data = dao.get_ratio_passed_chart_data(year)
        top_course_data = dao.get_top3_courses_chart_data(year)

        return self.render('admin/stats.html'
                           , years=years
                           , stats_students=stats_students
                           , stats_classes=stats_classes
                           , stats_total_revenue=stats_total_revenue
                           , stars_courses=stars_courses
                           , revenue_data=revenue_data
                           , student_data=student_data
                           , ratio_passed_data=ratio_passed_data
                           , top_course_data=top_course_data
                           , year=year)


# --- View Quy định học phí ---
class RegulationView(AdminBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        levels = dao.load_levels()
        if request.method == 'POST':
            try:
                for level in levels:
                    new_tuition = request.form.get(f'tuition_{level.id}')
                    if new_tuition:
                        # Gọi DAO để update (nhưng chưa commit)
                        dao.update_tuition_fee(level.id, new_tuition)

                # Commit 1 lần cuối cùng
                dao.save_changes()
                flash('Đã cập nhật học phí thành công!', 'success')
                return redirect(url_for('regulation.index'))
            except Exception as e:
                flash(f'Lỗi hệ thống: {str(e)}', 'danger')

        return self.render('admin/regulation.html', levels=levels)

############Chức năng của cashier##################
# LẬP HÓA ĐƠN
class CreateInvoiceView(CashierView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        search_kw = request.args.get('search')
        unpaid_regis = dao.get_unpaid_registrations(search_kw)

        student_info = None
        if search_kw and unpaid_regis:
            student_info = unpaid_regis[0].student

        if request.method == 'POST':
            try:
                regis_id = request.form.get('regis_id')
                amount = float(request.form.get('amount'))
                method = request.form.get('method')
                content = request.form.get('content')
                date_input = request.form.get('created_date')

                created_date = datetime.strptime(date_input, '%Y-%m-%d') if date_input else datetime.now()

                # Kiểm tra nợ
                regis = dao.get_registration_by_id(regis_id)
                current_debt = regis.actual_tuition - regis.paid

                if current_debt <= 0:
                    flash('Học viên đã hoàn tất học phí!', 'danger')
                elif amount > current_debt + 1000:
                    flash(f'Số tiền đóng lớn hơn nợ ({current_debt:,.0f}đ)!', 'danger')
                elif amount <= 0:
                    flash('Số tiền đóng phải lớn hơn 0!', 'danger')
                else:
                    # GỌI DAO ĐỂ XỬ LÝ THANH TOÁN (Gọn gàng hơn rất nhiều)
                    success, msg = dao.process_payment(
                        regis_id, amount, content, method, created_date, current_user.id
                    )
                    if success:
                        flash(f'Thu thành công {amount:,.0f}đ. {msg}', 'success' if 'hoàn tất' in msg else 'warning')

                return redirect(url_for('invoice.index'))

            except Exception as e:
                flash(f'Lỗi hệ thống: {str(e)}', 'danger')

        return self.render('admin/invoice_create.html',
                           student=student_info,
                           registrations=unpaid_regis,
                           today_str=datetime.now().strftime('%Y-%m-%d'))
#Quản lý hóa đơn
class TransactionAdminView(CashierModelView):
    can_create = False
    can_edit = False
    can_delete = True
    can_export = True
    export_types = ['csv']

    column_list = ('id', 'student_info', 'course_info', 'money', 'method', 'date', 'status', 'content')
    column_labels = dict(id='Mã HĐ', student_info='Học viên', course_info='Khóa học', money='Số tiền',
                         method='Hình thức', date='Ngày nộp', status='Trạng thái', content='Nội dung')
    column_default_sort = ('date', True)
    column_searchable_list = ['id', 'content', 'registration.student.account.name',
                              'registration.student.account.phone_num']
    column_filters = ['status', 'method', 'date', 'money', 'registration.student.account.name']

    def _student_formatter(view, context, model, name):
        if model.registration and model.registration.student and model.registration.student.account:
            return f"{model.registration.student.account.name} ({model.registration.student.account.phone_num})"
        return "N/A"

    def _course_formatter(view, context, model, name):
        if model.registration and model.registration.classroom and model.registration.classroom.course:
            return model.registration.classroom.course.name
        return "N/A"

    def _money_formatter(view, context, model, name):
        return "{:,.0f} đ".format(model.money)

    column_formatters = {
        'student_info': _student_formatter, 'course_info': _course_formatter, 'money': _money_formatter
    }
    column_formatters_export = column_formatters

    # Gọi DAO
    def get_query(self):
        return dao.get_transaction_query_options(super().get_query())

    def get_count_query(self):
        return dao.get_transaction_query_options(super().get_count_query())

    # Gọi DAO để revert dữ liệu khi xóa
    def on_model_delete(self, model):
        dao.revert_payment(model.registration, model.money)

############Chức năng của teacher##################
class RollcallView(TeacherView):

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        employee = EmployeeInfo.query.filter_by(u_id=current_user.id).first()
        classes = Classroom.query.filter_by(employee_id=employee.id).all() if employee else []

        if request.method == 'POST':
            session_id = request.form.get('session_id')

            if not session_id:
                flash("Vui lòng chọn buổi học!", "warning")

                class_id = request.form.get('class_id')

                sessions = Session.query.filter_by(class_id=class_id).all()
                regs = Registration.query.filter_by(class_id=class_id).all()

                return self.render(
                    'admin/rollcall.html',
                    classes=classes,
                    sessions=sessions,
                    student=regs
                )

            student_status = {}

            for k, v in request.form.items():
                if k.isdigit():  # CHỈ NHẬN key là số
                    student_status[int(k)] = int(v)
            dao.save_attendance(int(session_id), student_status)
            flash("Đã lưu điểm danh thành công!", "success")
            return redirect(url_for('.index'))

        return self.render('admin/rollcall.html', classes=classes, sessions=[], student=[])

    @expose('/load-by-class')
    def load_by_class(self):
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({'students': [], 'sessions': []})

        employee = EmployeeInfo.query.filter_by(
            u_id=current_user.id
        ).first()

        if not employee:
            return jsonify({'students': [], 'sessions': []})

        classroom = Classroom.query.filter_by(
            id=class_id,
            employee_id=employee.id
        ).first()

        if not classroom:
            return jsonify({'students': [], 'sessions': []})

        # Buổi học
        sessions = Session.query.filter(class_id==class_id).all()

        # Học viên trong lớp
        regs = Registration.query.filter_by(class_id=class_id).all()
        students = [r.student for r in regs]

        return jsonify({
            'sessions': [
                {
                    'id': s.id,
                    'name': f'Buổi {i + 1} - {s.session_content}',
                } for i, s in enumerate(sessions)
            ],
            'students': [
                {
                    'id': stu.id,
                    'name': stu.account.name
                } for stu in students
            ]
        })

class EnterScoreView(TeacherView):

    @expose('/', methods=['GET'])
    def index(self):
        employee = EmployeeInfo.query.filter_by(u_id=current_user.id).first()
        classes = Classroom.query.filter_by(employee_id=employee.id).all() if employee else []

        class_id = request.args.get('class_id', type=int)
        categories = GradeCategory.query.filter_by(active=1).all()
        students = []

        if class_id:
            regs = Registration.query.filter_by(class_id=class_id).all()
            for r in regs:
                score_map = {s.grade_cate_id: s.value for s in r.scores}
                total = 0
                weight_sum = 0
                scores_dict = {}

                for c in categories:
                    val = score_map.get(c.id)
                    scores_dict[c.id] = val
                    if val is not None:
                        total += val * c.weight
                        weight_sum += c.weight

                dtb = round(total / weight_sum, 2) if weight_sum > 0 else 0

                students.append({
                    'reg': r,
                    'scores': scores_dict,
                    'dtb': dtb
                })

        return self.render(
            'admin/enterscore.html',
            classes=classes,
            selected_class=class_id,
            categories=categories,
            students=students
        )

    @expose('/save-scores', methods=['POST'])
    def save_scores(self):
        for key, value in request.form.items():
            if key.startswith("score_"):
                _, reg_id, cate_id = key.split("_")
                reg_id, cate_id = int(reg_id), int(cate_id)
                val = float(value) if value else None

                score = Score.query.filter_by(regis_id=reg_id, grade_cate_id=cate_id).first()
                if score:
                    score.value = val
                else:
                    if val is not None:
                        db.session.add(Score(regis_id=reg_id, grade_cate_id=cate_id, value=val))
        db.session.commit()
        flash("Đã lưu điểm thành công!", "success")
        return redirect(request.referrer)
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

        if current_user.is_authenticated:
            return self.render('admin/home.html')
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
admin.add_view(AdminView(EmployeeInfo, db.session, name='Nhân viên', category='Người dùng'))
admin.add_view(AdminView(StudentInfo, db.session, name='Học viên', category='Người dùng'))
admin.add_view(RegulationView(name='Quy định', endpoint='regulation'))

# --- Menu cho CASHIER ---
admin.add_view(CreateInvoiceView(name='Lập hóa đơn', endpoint='invoice'))
admin.add_view(TransactionAdminView(Transaction, db.session, name='Quản lý giao dịch', endpoint='transaction'))

# --- Menu cho TEACHER ---
admin.add_view(RollcallView(name="Điểm danh", endpoint="rollcall"))
admin.add_view(EnterScoreView(name="Nhập điểm", endpoint="enterscore"))

# --- Menu chung ---
admin.add_view(MyLogoutView(name='Đăng xuất'))

if __name__ == '__main__':
    app.run(debug=True)