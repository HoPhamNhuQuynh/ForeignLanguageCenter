import random
import smtplib
from email.mime.text import MIMEText

from flask import render_template, request, redirect, make_response, session
from sqlalchemy.testing.exclusions import succeeds_if
from sqlalchemy.util import methods_equivalent

from foreignlanguage import app, admin, dao, login, db
from flask_login import current_user, login_user, logout_user
import cloudinary.uploader
from decorators import anonymous_required
from foreignlanguage.models import Student


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    err_msg = None
    if request.method.__eq__("POST"):
        username = request.form.get("username")
        password = request.form.get("password")
        remmember = request.form.get("rememberMe") == "true"

        user = dao.auth_user(username, password)

        if user:
            login_user(user, remember=remmember)
            return redirect("/")
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("signin.html", err_msg=err_msg)


@app.route("/signup", methods=["GET", "POST"])
@anonymous_required
def signup():
    err_msg = None
    if request.method.__eq__("POST"):
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if password.__eq__(confirm):
            name = request.form.get("name")
            phone_num = request.form.get("phone_num")
            username = request.form.get("username")
            email = request.form.get("email")
            address = request.form.get("address")

            existing_user = dao.auth_user(username, password)
            if existing_user:
                err_msg = "Username đã tồn tại!"
            else:
                try:
                    dao.add_user(name=name, phone_num=phone_num, username=username, password=password, email=email, address=address)
                    return redirect("/logout")
                except:
                    db.session.rollback()
                    err_msg = "Hệ thống đang bị lỗi! Vui lòng quay lại sau!"
        else:
            err_msg = "Mật khẩu không trùng khớp!"
    return render_template("signup.html", err_msg=err_msg)

@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect("/")


@app.route("/course")
def course():
    return render_template("course.html")


@app.route("/student")
def student():
    return render_template("student.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact_us():
    return render_template("contact.html")


@app.route("/entry-test")
def entry_test():
    return render_template("entry-test.html")

@app.route("/register-course")
def register_course():
    return render_template("register-form.html")


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
