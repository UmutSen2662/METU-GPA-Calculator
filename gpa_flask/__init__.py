from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask import Flask
from os import popen

app = Flask(__name__, template_folder="templates", static_folder="static")
app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
app.secret_key = "6e3fa0b943bdd99b572f14ffb792f935679a10a83010ce36784a47a5632c7b2b"

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="MetuGpaCalculato",
    password="dbpassword",
    hostname="MetuGpaCalculator.mysql.pythonanywhere-services.com",
    databasename="MetuGpaCalculato$default",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
if popen('hostname').read() == "TUF\n":
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "metugpaclaculator@gmail.com"
app.config["MAIL_PASSWORD"] = "jhsx vnwv ptgv eitt"
mail = Mail(app)

from gpa_flask import routes
