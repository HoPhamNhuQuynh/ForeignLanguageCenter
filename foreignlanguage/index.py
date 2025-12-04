from flask import render_template, request
from sqlalchemy.util import methods_equivalent

from foreignlanguage import app, admin, dao, login
from flask_login import current_user, login_user, logout_user

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    return render_template("signin.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    return render_template("signup.html")

@app.route("/course")
def course():
    return render_template("course.html")

@app.route("/student")
def student():
    return render_template("student.html")

@app.route("/about")
def about():
    return render_template("about.html")

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)