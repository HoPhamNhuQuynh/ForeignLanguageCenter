from flask import redirect
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from foreignlanguage.models import Student, Course, Classroom, Employee, UserRole

from foreignlanguage import app, db
from flask_login import login_required, current_user, logout_user

# class AdminView(ModelView):
#     def is_accessible(self) -> bool:
#         return current_user.is_authenticated and current_user.role == UserRole.ADMIN

# class LogoutView(BaseView):
#     @expose('/')
#     def __index__(self):
#         logout_user()
#         return redirect('/admin')

    # def is_accessible(self) -> bool:
    #     return current_user.is_authenticated

admin = Admin(app=app, name='ANQUINKO Administrator', theme=Bootstrap4Theme(), index_view=AdminIndexView())

admin.add_view(ModelView(Course, db.session))
admin.add_view(ModelView(Student, db.session))
admin.add_view(ModelView(Classroom, db.session))
admin.add_view(ModelView(Employee, db.session))
# admin.add_view(LogoutView(name='Đăng xuất'))
