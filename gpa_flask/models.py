from gpa_flask.__init__ import db, login_manager
from flask_login import UserMixin

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

class Course(db.Model):
    __tablename__ = "course"
    id = db.Column("id", db.Integer, primary_key = True)
    season = db.Column("season", db.Integer, nullable = False)
    name = db.Column("name", db.Text, nullable = False)
    credit = db.Column("credit", db.Integer, nullable = False)
    grade = db.Column("grade", db.Text, nullable = False)
    user = db.Column("User", db.ForeignKey("user.id"), nullable = False)

    def __init__(self, season, user):
        self.name = ""
        self.credit = 0
        self.grade = "XX"
        self.season = season
        self.user = user
