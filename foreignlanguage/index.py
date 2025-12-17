import random
from flask_mail import Message
from flask import render_template, request, redirect, session, url_for, jsonify
from foreignlanguage import app, dao, login, db, mail, admin
from flask_login import login_user, logout_user, current_user, login_required
from decorators import anonymous_required
from openpyxl import Workbook
from flask import send_file


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signin", methods=["GET", "POST"])
@anonymous_required
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
        confirm = request.form.get("confirm_pass")

        if password.__eq__(confirm):
            username = request.form.get("username")
            email = request.form.get("email")
            address = request.form.get("address")

            existing_user = dao.auth_user(username, password)
            if existing_user:
                err_msg = "Username đã tồn tại!"
            elif dao.check_email(email):
                err_msg = "Email đã tồn tại!"
            else:
                try:
                    dao.add_user(username=username, password=password, email=email, address=address)
                    return redirect("/signin")
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

@app.route("/forgot-pass", methods=["GET", "POST"])
def forgot_password():
    err_msg = None
    success_msg = None
    step = session.get("step", 1)

    if request.method.__eq__("POST"):
        if step == 1:
            email = request.form.get("email")
            user = dao.get_user_by_email(email=email)
            if user:
                otp = str(random.randint(100000, 999999))
                session['otp'] = otp
                session['email'] = email
                session['step'] = 2

                msg = Message(subject="Mã OTP",
                              sender= app.config['MAIL_USERNAME'],
                              recipients=[email],
                              body=f"Mã xác thực của bạn là: {otp}")
                mail.send(msg)
                success_msg = "Mã xác thực đã được gửi đến email của bạn."
            else:
                err_msg = "Email khômg tồn tại!"
        elif step == 2:
            otp = request.form.get("otp")
            if otp.__eq__(session['otp']):
                session['step'] = 3
            else:
                err_msg = "Nhập sai OTP!"
        elif step == 3:
            new_password = request.form.get("password")
            confirm = request.form.get("confirm")

            if new_password.__eq__(confirm):
                email = session.get("email")
                user = dao.get_user_by_email(email=email)
                if user:
                    dao.update_user_password(new_password, user.id)

                    session.pop('otp', None)
                    session.pop('email', None)
                    session.pop('step', None)

                    success_msg = "Đổi mật khẩu thành công!"
                    return redirect("/signin")
                else:
                    err_msg = "Người dùng không tồn tại!"
            else:
                err_msg = "Mật khẩu không trùng khớp!"

    return render_template("forgot-pass.html", step=session.get("step", 1), err_msg=err_msg, success_msg=success_msg)

@app.route("/courses/<int:id>")
def course(id):
    c = dao.get_course_by_id(id)
    return render_template("course.html", course=c)


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

@app.route("/register-course", methods=["GET", "POST"])
def register_course():
    # if not current_user.is_authenticated:
    #     return redirect("/signin")
    payment_methods = dao.get_payment_methods()
    return render_template("register-form.html", payment_methods=payment_methods)

@app.route("/api/tuition")
def get_tuition():
    class_id = request.args.get("class_id", type=int)
    tuition= dao.get_tuition_by_class_id(class_id=class_id)
    return jsonify({
        "tuition": tuition
    })


@app.route("/api/classes", methods=["GET"])
def get_classes():
    course_id = request.args.get("course_id", type=int)
    level_id = request.args.get("level_id", type=int)

    if not course_id or not level_id:
        return jsonify([])

    classes = dao.get_classes_by_course_level(course_id, level_id)
    res = []
    for c in classes:
        res.append({
            "id": c.id,
            "start_time": c.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "maximum_stu": c.maximum_stu,
            "current_count": c.current_count
        })
    return jsonify(res)

@app.route("/api/registrations", methods=["POST"])
def add_registration():
    pass


@app.route("/user-profile")
def user_profile():
    return render_template("student.html")


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

@app.context_processor
def common_attributes():
    return {
    'courses': dao.load_courses(),
    'levels'  :dao.load_levels()
    }

@app.route("/")
def home():
    return redirect(url_for('admin.index'))

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
