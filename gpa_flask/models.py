from gpa_flask.__init__ import db, login_manager, app
from datetime import datetime, timedelta, timezone
from flask_login import UserMixin
from jwt import encode, decode

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.Text, nullable = False)
    password = db.Column(db.Text, nullable = False)
    years = db.Column(db.Integer, nullable = False, default=4)

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def get_id(self):
        return self.id
    
    def get_token(self, expiration = 600):
        reset_token = encode(
            {
                "user_id": self.id,
                "exp": datetime.now(tz = timezone.utc) + timedelta(seconds = expiration)
            },
            app.config['SECRET_KEY'],
            algorithm = "HS256"
        )
        return reset_token

    @staticmethod
    def confirm_token(token):
        try:
            data = decode(
                token,
                app.config['SECRET_KEY'],
                leeway = timedelta(seconds = 10),
                algorithms = ["HS256"]
            )
        except:
            return None
        return User.query.get(data["user_id"])


class Course(db.Model):
    __tablename__ = "course"
    id = db.Column("id", db.Integer, primary_key = True)
    season = db.Column("season", db.Integer, nullable = False)
    name = db.Column("name", db.Text, nullable = False)
    credit = db.Column("credit", db.Integer, nullable = False)
    grade = db.Column("grade", db.Text, nullable = False)
    user = db.Column("user", db.ForeignKey("user.id"), nullable = False)

    def __init__(self, season, user):
        self.season = season
        self.name = ""
        self.credit = 0
        self.grade = "XX"
        self.user = user
