from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask import Flask

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
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
#app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

from gpa_flask import routes
