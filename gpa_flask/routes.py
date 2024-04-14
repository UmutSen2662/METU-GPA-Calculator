from flask import render_template, url_for, redirect, flash, request, session
from flask_login import login_user, logout_user, current_user
from gpa_flask.__init__ import app, db, bcrypt
from gpa_flask.models import User, Course

def calc_GPA(course_list):
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
    course_list = []
    for i in range(session["years"] * 3):
        courses = Course.query.filter(Course.season == i, Course.user == current_user.id)
        course_list.append([
            dict(id = course.id, name = course.name, credit = course.credit, grade = course.grade)
            for course in courses
        ])
    return course_list

@app.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("signin"))
    if "current_year" not in session:
        session["current_year"] = 1
    session["years"] = current_user.years
    course_list = get_list()
    return render_template("index.html", course_list = course_list, years = session["years"], current_year = session["current_year"], GPAs = calc_GPA(course_list))


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        if not current_user.is_authenticated:
            return render_template("signin.html")
        return redirect(url_for("index"))
    else:
        email = request.form["email"]
        user = User.query.filter(User.email == email).first()
        if user is None:
            flash("Account does not exist, try registering.", "error")
            return redirect(url_for("signin"))
        password = request.form["password"]
        if not bcrypt.check_password_hash(user.password, password):
            flash("Password is incorrect!", "error")
            return redirect(url_for("signin"))
        login_user(user)
        return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if not current_user.is_authenticated:
            return render_template("register.html")
        return redirect(url_for("index"))
    else:
        email = request.form["email"]
        if User.query.filter(User.email == email).first() is not None:
            flash("Email already in use try signing in!", "info")
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


@app.route("/recovery_page", methods=["GET", "POST"])
def recovery_page():
    if request.method == "GET":
        return redirect(url_for("signin"))
    else:
        flash("Recovery email has been sent!", "info")
        return redirect(url_for("signin"))


@app.route("/change_password", methods=["POST"])
def change_password():
    password = request.form["password"]
    if not bcrypt.check_password_hash(current_user.password, password):
        flash("Incorrect password, password change is unsuccessful!", "error")
        return redirect(url_for("index"))
    hashed_password = bcrypt.generate_password_hash(request.form["password1"])
    User.query.filter(User.id == current_user.id).update({User.password: hashed_password})
    db.session.commit()
    flash("Password change successful!", "info")
    return redirect(url_for("index"))


@app.route("/change_year/<int:year>", methods=["GET"])
def change_year(year):
    session["current_year"] = year
    return "", 204


@app.route("/edit_year/<int:value>", methods=["GET"])
def edit_year(value):
    if session["years"] > 1:
        session["years"] += value - 2
        if session["current_year"] > session["years"]:
            session["current_year"] = session["years"]
        current_user.years = session["years"]
        if value == 1:
            for i in range(3):
                Course.query.filter(Course.season == (session["years"] * 3 + i), Course.user == current_user.id).delete()
        db.session.commit()
    return redirect(url_for("index"))


@app.route("/add_course/<int:season>", methods=["GET"])
def add_course(season):
    course = Course(season=season, user=current_user.id)
    db.session.add(course)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/delete_course/<int:cid>", methods=["GET"])
def delete_course(cid):
    Course.query.filter(Course.id == cid).delete()
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/change_course", methods=["POST"])
def change_course():
    cid =  request.form["id"]
    value =  request.form["value"]
    change = cid[:1]
    cid = int(cid[1:])

    if change == "i":
        Course.query.filter(Course.id == cid).update({Course.name: value})
    elif change == "c":
        Course.query.filter(Course.id == cid).update({Course.credit: value})
    elif change == "g":
        Course.query.filter(Course.id == cid).update({Course.grade: value})
    db.session.commit()
    return calc_GPA(get_list())
