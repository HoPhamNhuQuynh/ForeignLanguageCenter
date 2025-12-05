from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user, logout_user
from sqlalchemy import func

# Import app, db và models từ project của bạn
from foreignlanguage import app, db
from foreignlanguage.models import (
    Student, Course, Classroom, Employee,
    Registration, Transaction, Score, UserRole, Level
)


# 1. Custom lại ModelView để bảo mật
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        # return current_user.is_authenticated and current_user.role == UserRole.ADMIN
        return True

    # 2. View Báo cáo (Trang chủ)


class ReportView(AdminIndexView):
    @expose('/')
    def index(self):
        # Thống kê
        stu_count = Student.query.count()

        revenue_data = db.session.query(func.sum(Transaction.money)).scalar()
        total_revenue = revenue_data if revenue_data else 0

        pass_count = Score.query.filter(Score.value >= 5.0).count()
        total_scores = Score.query.count()
        pass_rate = round((pass_count / total_scores * 100), 1) if total_scores > 0 else 0

        return self.render('admin/report.html',
                           stu_count=stu_count,
                           total_revenue=total_revenue,
                           pass_rate=pass_rate)


# 3. View Thay đổi quy định
class RegulationView(BaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        levels = Level.query.all()
        default_max_stu = 25

        if request.method == 'POST':
            try:
                for level in levels:
                    new_tuition = request.form.get(f'tuition_{level.id}')
                    if new_tuition:
                        level.tuition = float(new_tuition)

                new_max_stu = request.form.get('max_stu')
                print(f"Sỉ số lớp mới: {new_max_stu}")

                db.session.commit()
                flash('Cập nhật quy định thành công!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Có lỗi xảy ra: {str(e)}', 'error')

        return self.render('admin/regulation.html',
                           levels=levels,
                           max_stu=default_max_stu)


# 4. View Đăng xuất
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')


# 5. KHỞI TẠO ADMIN VÀ SẮP XẾP MENU
# ============================================================

# Bước 1: Khởi tạo với index_view là ReportView -> "Báo cáo" sẽ luôn đứng đầu
admin = Admin(
    app=app,
    name='ANQUINKO',
    theme=Bootstrap4Theme(),
    index_view=ReportView(name='Báo cáo', url='/admin')
)

# Bước 2: Thêm nhóm "Quản lí khóa học"
admin.add_view(AuthenticatedModelView(Course, db.session, name='Khóa học', category='Quản lí khóa học'))
admin.add_view(AuthenticatedModelView(Classroom, db.session, name='Lớp học', category='Quản lí khóa học'))

# Bước 3: Thêm "Thay đổi quy định" (Không để category để nó hiện ra ngoài làm mục chính)
admin.add_view(RegulationView(name='Thay đổi quy định', endpoint='regulation'))

# Bước 4: Thêm nhóm "Thông tin nhân sự" (Đã đổi tên từ 'Thông tin cá nhân')
admin.add_view(AuthenticatedModelView(Student, db.session, name='Học viên', category='Thông tin nhân sự'))
admin.add_view(AuthenticatedModelView(Employee, db.session, name='Nhân viên', category='Thông tin nhân sự'))

# Bước 5: Thêm nút Đăng xuất cuối cùng
admin.add_view(LogoutView(name='Đăng xuất'))

if __name__ == '__main__':
    app.run(debug=True)