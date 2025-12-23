from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import cloudinary

app = Flask(__name__)
app.secret_key = "asjdahjsdaskdjahsd%#adsd"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Nhuquynh261105%40@localhost/centerdb?charset=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

cloudinary.config(cloud_name='dv71msurs',
                  api_key='985628496422912',
                  api_secret='U9DEvl23WcSyDM34N0yH--Lcqyw')

app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'mydanh1177@gmail.com'
app.config['MAIL_PASSWORD'] = 'lvmg fuxh uyzg otpy'
app.config['MAIL_DEFAULT_SENDER'] = 'mydanh1177@gmail.com'
mail = Mail(app)

db = SQLAlchemy(app)
login = LoginManager(app)

login.login_view = "signin"
login.login_message = "Vui lòng đăng nhập để tiếp tục!"
login.login_message_category = "info"
