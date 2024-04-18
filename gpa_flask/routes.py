from flask import render_template, url_for, redirect, flash, request, session
from flask_login import login_user, logout_user, current_user
from gpa_flask.__init__ import app, db, bcrypt, mail
from gpa_flask.models import User, Course
from flask_mail import Message

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

    seen_list = []
    GPAs = []
    CGPAs = []
    for season in course_list:
        total_grades = 0
        total_credits = 0
        current_grades = 0
        current_credits = 0
        for course in season:
            for old in seen_list:
                if old["name"] == course["name"]:
                    seen_list.remove(old)
            seen_list.append(course)
            current_grades += grade_int(course["grade"]) * course["credit"]
            current_credits += course["credit"]
        for course in seen_list:
            total_grades += grade_int(course["grade"]) * course["credit"]
            total_credits += course["credit"]
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
        if user is not None:
            password = request.form["password"]
            if bcrypt.check_password_hash(user.password, password):
                login_user(user, remember = True)
                return redirect(url_for("index"))
        flash("The email and/or password do not match.", "error")
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
    flash("You have successfully signed out!", "info")
    return redirect(url_for("signin"))


def send_mail(user):
    token = user.get_token()
    msg = Message("Password reset request", recipients = [user.email], sender="noreply@metugpaclaculator.com")
    msg.body = f'''
    To reset your password please follow the link below.

    {url_for("reset_password", token = token, _external = True)}
    If you did't send a password reset request, please ignore this message.
    '''
    mail.send(msg)

@app.route("/recovery_page", methods=["GET", "POST"])
def recovery_page():
    if request.method == "GET":
        return render_template("recovery_page.html")
    else:
        email = request.form["email"]
        user = User.query.filter(User.email == email).first()
        if user is not None:
            send_mail(user)
        flash("Recovery email has been sent!", "info")
        return redirect(url_for("signin"))


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.confirm_token(token)
    if user is None:
        flash("Token is invalid or expired! Please try again.", "error")
        return redirect(url_for("recovery_page"))
    if request.method == "GET":
        return render_template("reset_password.html")
    else:
        hashed_password = bcrypt.generate_password_hash(request.form["password1"])
        user.password = hashed_password
        db.session.commit()
        flash("Password changed succesfully", "info")
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
    return ""


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
    return f"""
    <div id="{course.id}" class="course">
        <button class="deleteButton" hx-delete="/delete_course/{course.id}" hx-swap="outerHTML" hx-target="closest .course">X</button>
        <span><input name="name" id="i{course.id}" type="text" placeholder="Enter course Name" value="" list="courses" autocomplete="off"></span>
        <span><input name="credit" id="c{course.id}" type="number" style="text-align: center;" min="0" value="0" onclick="this.select()" autocomplete="off"></span>
        <select name="grade" id="g{course.id}">
            <option value="XX" selected>XX</option>
            <option value="AA">AA</option>
            <option value="BA">BA</option>
            <option value="BB">BB</option>
            <option value="CB">CB</option>
            <option value="CC">CC</option>
            <option value="DC">DC</option>
            <option value="DD">DD</option>
            <option value="FD">FD</option>
            <option value="FF">FF</option>
            <option value="NA">NA</option>
            <option value="S">S</option>
            <option value="U">U</option>
        </select>
    </div>
    """


@app.route("/delete_course/<int:cid>", methods=["DELETE"])
def delete_course(cid):
    course = Course.query.filter(Course.id == cid).first()
    if course.user == current_user.id:
        Course.query.filter(Course.id == cid).delete()
        db.session.commit()
        return ""
    return 500


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


@app.route("/get_gpa", methods=["get"])
def get_gpa():
    return calc_GPA(get_list())
