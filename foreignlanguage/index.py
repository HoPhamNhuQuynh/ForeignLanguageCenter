from flask import render_template, request
from foreignlanguage import app

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/course")
def course():
    return render_template("course.html")

@app.route("/student")
def student():
    return render_template("student.html")

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)