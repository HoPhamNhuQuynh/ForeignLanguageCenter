import hashlib
import io
import math
from datetime import datetime
import pandas as pd
from flask import redirect, request, flash, url_for, jsonify, send_file
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user, login_user, logout_user
from markupsafe import Markup

from foreignlanguage import app, db, login, email_service
from foreignlanguage.models import (
    Registration, StudentInfo, Course, Classroom, EmployeeInfo,
    Transaction, UserRole, Score, Present,
    Session, GradeCategory, AcademicStatus, StatusPayment, UserAccount, CourseLevel
)
from foreignlanguage import dao


class AuthenticationView(ModelView):
    def __init__(self, model, session, role=None, *args, **kwargs):
        self.required_role = role
        super().__init__(model, session, *args, **kwargs)

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.role == self.required_role


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


################ ADMIN ####################
# --- Báo cáo Dashboard ---
class StatsView(AdminBaseView):
    @expose('/')
    def index(self):
        can_export = True

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
    @expose('/export')
    def export_report(self):
        year = request.args.get('year', type=int, default=datetime.now().year)
        stats_summary = {
            'Học viên': [dao.count_students(year)],
            'Khóa học': [dao.count_courses(year)],
            'Lớp học': [dao.count_active_classes(year)],
            'Tổng doanh thu': [dao.count_total_revenue(year)]
        }
        revenue_raw = dao.get_revenue_chart_data(year)
        student_raw = dao.get_student_chart_data(year)
        ratio_passed_raw = dao.get_ratio_passed_chart_data(year)
        top_course_raw = dao.get_top3_courses_chart_data(year)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            pd.DataFrame(stats_summary).to_excel(writer, index=False, sheet_name='Tổng quan')
            pd.DataFrame({
                'Tháng': revenue_raw.get('labels', []),
                'Doanh thu (VNĐ)': revenue_raw.get('data', [])
            }).to_excel(writer, index=False, sheet_name='Doanh thu')
            pd.DataFrame({
                'Nhóm học viên': student_raw.get('labels', []),
                'Số lượng': student_raw.get('data', [])
            }).to_excel(writer, index=False, sheet_name='Học viên')
            pd.DataFrame({
                'Trạng thái': ratio_passed_raw.get('labels', []),
                'Số lượng': ratio_passed_raw.get('data', [])
            }).to_excel(writer, index=False, sheet_name='Tỷ lệ đạt')
            pd.DataFrame({
                'Khóa học': top_course_raw.get('labels', []),
                'Doanh thu/Số lượng': top_course_raw.get('data', [])
            }).to_excel(writer, index=False, sheet_name='Top khóa học')

        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"Bao_cao_tong_hop_{year}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# --- View Quy định học phí ---
class RegulationView(AdminBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        course_levels = dao.get_all_course_levels()

        if request.method == 'POST':
            try:
                for item in course_levels:
                    input_name = f'tuition_{item.course_id}_{item.level_id}'
                    new_tuition = request.form.get(input_name)

                    if new_tuition and float(new_tuition) != item.tuition:
                        # Truyền cả 2 ID vào DAO
                        dao.update_course_level_tuition(item.course_id, item.level_id, new_tuition)

                dao.db.session.commit()
                flash('Đã cập nhật bảng giá học phí thành công!', 'success')
                return redirect(url_for('regulation.index'))

            except Exception as e:
                flash(f'Lỗi hệ thống: {str(e)}', 'danger')

        return self.render('admin/regulation.html', course_levels=course_levels)

class CourseLevelAdminView(AdminView):
    column_list = ('course_id', 'level_id')

    column_labels = dict(
        course_id='Id khóa học',
        level_id='Các level id'
    )

class CourseAdminView(AdminView):
    column_list = ('name', 'description', 'period', 'content', 'joined_date', 'active')

    column_labels = dict(
        name='Tên khóa học',
        description='Mô tả',
        period='Thời lượng (tháng)',
        content='Nội dung đào tạo',
        joined_date='Ngày tạo',
        active='Trạng thái'
    )

class ClassroomAdminView(AdminView):
    can_edit = True
    column_list = ('id', 'course_info', 'start_time', 'maximum_stu', 'employee_name', 'joined_date', 'active')

    column_labels = dict(
        id='Mã lớp',
        course_info='Khóa học - Cấp độ',
        start_time='Ngày khai giảng',
        maximum_stu='Sĩ số tối đa',
        employee_name='Giáo viên chủ nhiệm',
        joined_date='Ngày tạo',
        active='Trạng thái'
    )
    column_searchable_list = ['id']
    column_sortable_list = ['id', 'start_time', 'maximum_stu', 'active']

    def _employee_formatter(view, context, model, name):
        if model.employee and model.employee.account:
            return model.employee.account.name
        return "Chưa phân công"

    def _course_level_formatter(view, context, model, name):
        course_name = model.course_level.course.name if model.course_level.course else "N/A"
        level_name = model.course_level.level.name if model.course_level.level else "N/A"
        return f"{course_name} ({level_name})"

    # Gán formatter vào các cột
    column_formatters = {
        'employee_name': _employee_formatter,
        'course_info': _course_level_formatter,
    }

class EmployeeAdminView(AdminView):
    can_edit = True
    column_list = ('account.name', 'base_salary', 'account.joined_date', 'account.active')

    column_labels = dict(
        base_salary='Lương cơ bản',
        **{'account.name': 'Tên nhân viên',
           'account.joined_date': 'Ngày vào làm',
           'account.active': 'Trạng thái'}
    )

class StudentAdminView(AdminView):
    can_edit = True
    column_list = ('account.name', 'entry_score', 'account.joined_date', 'account.active')

    column_labels = dict(
        entry_score='Điểm đầu vào',
        **{'account.name': 'Họ tên học viên',
           'account.joined_date': 'Ngày nhập học',
           'account.active': 'Trạng thái'}
    )

class AccountAdminView(AdminView):
    can_edit = True
    column_list = ('name', 'username', 'password', 'email', 'role', 'active')

    column_labels = {
        'name': 'Tên',
        'username': 'Tên đăng nhập',
        'password': 'Mật khẩu',
        'email': 'Email',
        'role': 'Vai trò',
        'active': 'Trạng thái'
    }
    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password = hashlib.md5(
                form.password.data.encode('utf-8')
            ).hexdigest()


############Chức năng của cashier##################
# LẬP HÓA ĐƠN
class CreateInvoiceView(CashierView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        # ===== XỬ LÝ LẬP PHIẾU THU =====
        if request.method == 'POST':
            regis_id = request.form.get('regis_id')
            amount = request.form.get('amount')
            method = request.form.get('payment_method')
            content = request.form.get('content')

            if not regis_id or not amount or not method:
                flash("Vui lòng nhập đầy đủ thông tin thanh toán!", "danger")
                return redirect(url_for('.index'))

            success, msg = dao.register_and_pay_by_cashier(
                regis_id=int(regis_id),
                amount=int(amount),
                content=content,
                method=method,
                employee_id=current_user.id
            )

            flash(msg, 'success' if success else 'danger')
            return redirect(url_for('.index'))

        # ===== GET – HIỂN THỊ DANH SÁCH NỢ =====
        search_kw = request.args.get('search')
        unpaid_regis = dao.get_unpaid_registrations(search_kw)

        student_info = None
        if search_kw and unpaid_regis:
            student_info = unpaid_regis[0].student

        courses = dao.load_courses()
        levels = dao.load_levels()
        students = dao.load_students()
        payment_methods = dao.get_payment_methods()

        return self.render(
            'admin/invoice_create.html',
            student=student_info,
            registrations=unpaid_regis,
            today_str=datetime.now().strftime('%Y-%m-%d'),
            courses=courses,
            levels=levels,
            students=students,
            payment_methods=payment_methods
        )

    # [MỚI] Xử lý nút Hủy bỏ -> Xóa đăng ký
    @expose('/delete-regis', methods=['POST'])
    def delete_regis(self):
        regis_id = request.form.get('regis_id')
        if regis_id:
            if dao.delete_registration(regis_id):
                flash('Đã xóa đăng ký thành công!', 'success')
            else:
                flash('Không tìm thấy đăng ký để xóa.', 'danger')
        return redirect(url_for('.index'))

    @expose('/create-manual', methods=['POST'])
    def create_manual(self):
        try:
            student_id = request.form.get('student_id')  # UserAccount ID
            class_id = request.form.get('class_id')
            payment_percent = request.form.get('payment_percent')
            method = request.form.get('payment_method')

            # ===== VALIDATE =====
            if not student_id or not class_id or not payment_percent or not method:
                flash('Vui lòng nhập đầy đủ thông tin!', 'danger')
                return redirect(url_for('.index'))

            student_id = int(student_id)
            class_id = int(class_id)
            payment_percent = int(payment_percent)

            # ===== TÍNH HỌC PHÍ =====
            real_tuition = dao.get_tuition_by_class_id(class_id)
            if not real_tuition:
                flash('Không xác định được học phí lớp học!', 'danger')
                return redirect(url_for('.index'))

            amount = (
                real_tuition
                if payment_percent == 100
                else math.ceil(real_tuition / 2)
            )

            content = f"Thu ngân tạo đăng ký – Thanh toán {payment_percent}%"

            # ===== GỌI DAO =====
            success, msg = dao.create_manual_invoice(
                student_id=student_id,
                class_id=class_id,
                amount=amount,
                method=method,
                content=content,
                employee_id=current_user.id
            )
            if success:
                try:
                    # Lấy thông tin user
                    user = dao.get_user_by_id(student_id)
                    # Lấy thông tin lớp
                    classroom = dao.get_class_by_id(class_id)

                    if user and classroom:
                        full_class_name = f"{classroom.course_level.course.name} ({classroom.course_level.level.name})"

                        email_service.send_register_success_email(
                            to_email=user.email,
                            name=user.name,
                            class_name=full_class_name
                        )
                    flash(f'Tạo hóa đơn thành công! {msg}', 'success')
                except Exception as e:
                    print(f"Lỗi gửi mail (Manual): {e}")
                    flash(f'Tạo hóa đơn thành công nhưng lỗi gửi mail. {msg}', 'warning')
            else:
                flash(msg, 'danger')

        except Exception as e:
            flash(f'Lỗi hệ thống: {str(e)}', 'danger')

        return redirect(url_for('.index'))

    @expose('/load-classes')
    def load_classes(self):
        course_id = request.args.get('course_id')
        level_id = request.args.get('level_id')
        student_id = request.args.get('student_id')

        if not course_id or not level_id:
            return jsonify([])

        classes = dao.get_classes_by_course_level(course_id, level_id, student_id)

        data = []
        for c in classes:
            data.append({
                'id': c.id,
                # Format ngày tháng thành chuỗi dd/mm/yyyy
                'start_time': c.start_time.strftime('%d/%m/%Y'),
                'maximum_stu': c.maximum_stu,
                'current_count': c.current_count
            })

        return jsonify(data)

# Quản lý hóa đơn
class TransactionAdminView(CashierModelView):
    can_create = False
    can_edit = False
    can_delete = True

    column_list = ('id', 'student_info', 'course_info', 'money', 'method', 'joined_date', 'status', 'content', 'print_ticket')
    column_labels = dict(id='Mã HĐ', student_info='Học viên', course_info='Khóa học', money='Số tiền',
                         method='Hình thức', joined_date='Ngày nộp', status='Trạng thái', content='Nội dung',
                         print_ticket='Hành động')
    column_default_sort = ('joined_date', True)
    column_searchable_list = ['id']
    column_filters = ['status', 'method', 'joined_date', 'money']

    def _student_formatter(view, context, model, name):
        if model.registration and model.registration.student:
            return f"{model.registration.student.account.name}"
        return "N/A"

    def _course_formatter(view, context, model, name):
        if model.registration.classroom.course_level.course.name:
            return model.registration.classroom.course_level.course.name
        return "N/A"

    def _money_formatter(view, context, model, name):
        return "{:,.0f} đ".format(model.money)

    # Gọi DAO để revert dữ liệu khi xóa
    def on_model_delete(self, model):
        dao.revert_payment(model.registration, model.money)

    def delete_model(self, model):
        try:
            self.on_model_delete(model)
            model.status = StatusPayment.FAILED
            model.content = f"{model.content} [ĐÃ HỦY]"
            self.session.add(model)
            self.session.commit()
            return True

        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(f'Lỗi khi hủy giao dịch: {str(ex)}', 'danger')
            self.session.rollback()
            return False

    def _print_formatter(view, context, model, name):
        print_url = url_for('.print_view', id=model.id)
        return Markup(f'''
            <a href="{print_url}" target="_blank" class="btn btn-info btn-sm" title="In hóa đơn">
                <i class="fa fa-print"></i> In
            </a>
        ''')

    column_formatters = {
        'registration.student.account': _student_formatter,
        'student_info': _student_formatter,
        'course_info': _course_formatter,
        'money': _money_formatter,
        'print_ticket': _print_formatter  # Đăng ký formatter in
    }

    # 3. Tạo Route (Trang hiển thị phiếu in)
    @expose('/print/<int:id>')
    def print_view(self, id):
        # Lấy thông tin giao dịch (Có thể gọi qua DAO hoặc query trực tiếp)
        transaction = Transaction.query.get(id)

        if not transaction:
            return "Không tìm thấy giao dịch", 404

        # Render template in hóa đơn (Sẽ tạo ở bước 2)
        return self.render('admin/invoice_print.html', trans=transaction)


############Chức năng của teacher##################
class RollcallView(TeacherView):

    @expose('/', methods=['GET', 'POST'])
    def index(self):
        employee = dao.get_emloyee_by_user_id(current_user.id)
        classes = dao.get_teacher_classes(employee.id if employee else None)

        if request.method == 'POST':
            session_id = request.form.get('session_id')

            if not session_id:
                flash("Vui lòng chọn buổi học!", "warning")

                class_id = request.form.get('class_id')

                sessions = dao.get_sessions_by_class(class_id)
                regs = dao.get_regs_by_class(class_id)
                present = dao.get_present_by_session(session_id)
                attendance_dict = {p.student_id: (1 if p.is_present else 0) for p in present}

                return self.render(
                    'admin/rollcall.html',
                    classes=classes,
                    sessions=sessions,
                    student=regs,
                    attendance_dict=attendance_dict
                )

            student_status = {}

            for k, v in request.form.items():
                if k.startswith('student_'):
                    student_id = k.replace('student_', '')
                    if student_id.isdigit():
                        student_status[int(student_id)] = int(v)

            # Lúc này student_status sẽ là {6: 0} -> Hết rỗng!
            if dao.save_present(int(session_id), student_status):
                flash("Đã lưu điểm danh thành công!", "success")
            else:
                flash("Lưu điểm danh thất bại!", "danger")
            return redirect(url_for('.index'))

        return self.render('admin/rollcall.html', classes=classes, sessions=[], student=[])

    @expose('/api/load-by-class')
    def load_by_class(self):
        class_id = request.args.get('class_id')
        if not class_id:
            return jsonify({'students': [], 'sessions': []})

        employee = dao.get_emloyee_by_user_id(current_user.id)

        if not employee:
            return jsonify({'students': [], 'sessions': []})

        classroom = dao.get_classroom_by_teacher(class_id, employee.id)

        if not classroom:
            return jsonify({'students': [], 'sessions': []})

        sessions = dao.get_sessions_by_class(class_id)
        regs = dao.get_regs_by_class(class_id)
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

    @expose('/api/get-attendance')
    def get_attendance(self):
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({'attendance': {}})

        present = dao.get_present_by_session(session_id)

        result = {}
        for p in present:
            result[p.student_id] = 1 if p.is_present else 0

        return jsonify({'attendance': result})



class EnterScoreView(TeacherView):
    @expose('/', methods=['GET'])
    def index(self):
        employee = dao.get_emloyee_by_user_id(current_user.id)
        classes = dao.get_teacher_classes(employee.id if employee else [])

        class_id = request.args.get('class_id', type=int)
        categories = dao.get_active_grade_categories()
        students = []

        if class_id:
            regs = dao.get_regs_by_class(class_id)
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
        updated_regs = set()

        for key, value in request.form.items():
            if key.startswith("score_"):
                _, reg_id, cate_id = key.split("_")
                reg_id, cate_id = int(reg_id), int(cate_id)
                val = float(value) if value.strip() else 0

                score = dao.get_score_by_registration(reg_id, cate_id)
                if score:
                    score.value = val
                else:
                    if val is not None:
                        db.session.add(Score(regis_id=reg_id, grade_cate_id=cate_id, value=val))

                updated_regs.add(reg_id)

        for r_id in updated_regs:
            f_score_val = request.form.get(f"final_score_{r_id}")

            reg_record = dao.get_registration_by_id(r_id)
            if reg_record:
                reg_record.final_score = float(f_score_val) if f_score_val else 0

                if reg_record.final_score >= 5:
                    reg_record.academic_status = AcademicStatus.PASSED
                else:
                    reg_record.academic_status = AcademicStatus.FAILED

        try:
            db.session.commit()
            flash("Đã lưu điểm và kết quả thành công!", "success")
        except Exception as e:
            db.session.rollback()
            print(f"LỖI LƯU ĐIỂM: {str(e)}")
            flash(f"Lỗi hệ thống: {str(e)}", "danger")
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
admin.add_view(CourseAdminView(Course, db.session, name='Khóa học', category='Đào tạo'))
admin.add_view(CourseLevelAdminView(CourseLevel, db.session, name ='Cấp bậc lớp học', category='Đào tạo'))
admin.add_view(ClassroomAdminView(Classroom, db.session, name='Lớp học', category='Đào tạo'))
admin.add_view(AccountAdminView(UserAccount, db.session, name="Tài khoản", category='Người dùng'))
admin.add_view(EmployeeAdminView(EmployeeInfo, db.session, name='Nhân viên', category='Người dùng'))
admin.add_view(StudentAdminView(StudentInfo, db.session, name='Học viên', category='Người dùng'))
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

