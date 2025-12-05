from datetime import timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)
app.secret_key = "asjdahjsdaskdjahsd%#adsd"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Nhuquynh261105%40@localhost/centerdb?charset=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

cloudinary.config(cloud_name='dv71msurs',
                  api_key='985628496422912',
                  api_secret='U9DEvl23WcSyDM34N0yH--Lcqyw')

app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

db = SQLAlchemy(app)
login = LoginManager(app)

