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

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)