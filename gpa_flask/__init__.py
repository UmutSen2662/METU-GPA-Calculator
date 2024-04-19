from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import dotenv_values
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask import Flask

app = Flask(__name__, template_folder="templates", static_folder="static")

app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True
app.secret_key = dotenv_values(".env")["secret_key"]

cfg = dotenv_values(".cfg")
app.config.update(cfg)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

mail = Mail(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
unauthorized_handler = login_manager.unauthorized_handler

from gpa_flask import routes
