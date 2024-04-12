from flask import render_template, url_for, redirect, flash, request
from flask_login import login_user, logout_user, current_user
from gpa_flask.__init__ import app, db, bcrypt
from gpa_flask.models import User, Course

course_list = []
current_year = 1
years = 4

def calc_GPA():
    def grade_int(grade):
        match grade:
            case "AA": return 4
            case "BA": return 3.5
            case "BB": return 3
            case "CB": return 2.5
            case "CC": return 2
            case "DC": return 1.5
            case "DD": return 1
            case "FD": return 0.5
        return 0

    GPAs = []
    CGPAs = []
    total_grades = 0
    total_credits = 0
    for season in course_list:
        current_grades = 0
        current_credits = 0
        for course in season:
            current_grades += grade_int(course["grade"]) * course["credit"]
            current_credits += course["credit"]
        total_grades += current_grades
        total_credits += current_credits
        gpa = ("%.2f" % (current_grades/current_credits)).rstrip('0').rstrip('.') if current_credits > 0 else ""
        cgpa = ("%.2f" % (total_grades/total_credits)).rstrip('0').rstrip('.') if total_credits > 0 else ""
        GPAs.append(gpa)
        CGPAs.append(cgpa)
    data = str({"g": GPAs, "c": CGPAs}).replace("\'", "\"")
    return data

def get_list():
    global course_list
    course_list = []
    for i in range(years * 3):
        courses = Course.query.filter(Course.season == i, Course.user == current_user.id)
        course_list.append([
            dict(id = course.id, name = course.name, credit = course.credit, grade = course.grade)
            for course in courses
        ])


@app.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("signin"))
    global years
    years = current_user.years
    get_list()
    return render_template("index.html", course_list = course_list, years = years, current_year = current_year, GPAs = calc_GPA())


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        if not current_user.is_authenticated:
            return render_template("signin.html")
        return redirect(url_for("index"))
    else:
        email = request.form["email"]
        if User.query.filter(User.email == email).first() is not None:
            password = request.form["password"]
            user = User.query.filter(User.email == email).first()
            if user is not None:
                if bcrypt.check_password_hash(user.password, password):
                    login_user(user)
                    return redirect(url_for("index"))
        flash("Email or password is incorrect!")
        return redirect(url_for("signin"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if not current_user.is_authenticated:
            return render_template("register.html")
        return redirect(url_for("index"))
    else:
        email = request.form["email"]
        if User.query.filter(User.email == email).first() is not None:
            flash("Email already in use try logging in!")
            return redirect(url_for("signin"))
        hashed_password = bcrypt.generate_password_hash(request.form["password1"])
        user = User(email, hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("index"))


@app.route("/signout")
def signout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/change_password", methods=["POST"])
def change_password():
    password = request.form["password"]
    if not bcrypt.check_password_hash(current_user.password, password):
        flash("Incorrect password, password change is unsuccessful!")
        return redirect(url_for("index"))
    hashed_password = bcrypt.generate_password_hash(request.form["password1"])
    User.query.filter(User.id == current_user.id).update({User.password: hashed_password})
    db.session.commit()
    flash("Password change successful!")
    return redirect(url_for("index"))


@app.route("/change_year/<int:year>", methods=["GET"])
def change_year(year):
    global current_year
    current_year = year
    return "ok"


@app.route("/edit_year/<int:value>", methods=["GET"])
def edit_year(value):
    global years
    global current_year
    if years > 1:
        years += value - 2
        if current_year > years:
            current_year = years
        current_user.years = years
        if value == 1:
            for i in range(3):
                Course.query.filter(Course.season == (years * 3 + i), Course.user == current_user.id).delete()
        db.session.commit()
    return redirect(url_for("index"))


@app.route("/add_course/<int:season>", methods=["GET"])
def add_course(season):
    course = Course(season=season, user=current_user.id)
    db.session.add(course)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete_course/<int:id>", methods=["GET"])
def delete_course(cid):
    Course.query.filter(Course.id == cid).delete()
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/change_course", methods=["POST"])
def change_course():
    cid =  request.form["id"]
    value =  request.form["value"]
    change = cid[0:1]
    cid = int(cid[1:])

    if change == "i":
        Course.query.filter(Course.id == cid).update({Course.name: value})
    elif change == "c":
        Course.query.filter(Course.id == cid).update({Course.credit: value})
    elif change == "g":
        Course.query.filter(Course.id == cid).update({Course.grade: value})
    db.session.commit()
    get_list()
    return calc_GPA()
