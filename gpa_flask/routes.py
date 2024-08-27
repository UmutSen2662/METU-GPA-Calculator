from flask import Response, render_template, url_for, redirect, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from gpa_flask.__init__ import app, db, bcrypt, mail, unauthorized_handler, google_client
from gpa_flask.models import User, Course, GoogleID
import requests, json, math

def calc_GPA(course_list):
    def grade_int(grade):
        match grade:
            case "AA": return 400
            case "BA": return 350
            case "BB": return 300
            case "CB": return 250
            case "CC": return 200
            case "DC": return 150
            case "DD": return 100
            case "FD": return 50
            case "S": return 400
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
            if course["grade"] != "XX":
                if course["name"] != "":
                    for old in seen_list:
                        if old["name"] == course["name"]:
                            seen_list.remove(old)
                seen_list.append(course)
                current_grades += grade_int(course["grade"]) * course["credit"]
                current_credits += course["credit"]
        for course in seen_list:
            total_grades += grade_int(course["grade"]) * course["credit"]
            total_credits += course["credit"]
        gpa = ("%.2f" % (math.ceil(current_grades/current_credits)/100)).rstrip('0').rstrip('.') if current_credits > 0 else ""
        cgpa = ("%.2f" % (math.ceil(total_grades/total_credits)/100)).rstrip('0').rstrip('.') if total_credits > 0 else ""
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

def handle_csv(data):
    lines = data.splitlines()
    table = [line.split(",") for line in lines]

    if table[0] != ["Course Name", "Season", "Credit", "Grade"]:
        return
    
    for row in table[1:]:
        match = Course.query.filter(Course.name == row[0], Course.season == row[1], Course.credit == row[2], Course.grade == row[3])
        if match.count() == 0:
            course = Course(season = row[1], name = row[0], credit = row[2], grade = row[3], user = current_user.id)
            db.session.add(course)
            db.session.commit()

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        session.setdefault("current_year", 1)
        session["years"] = current_user.years
        course_list = get_list()
        return render_template("index.html", course_list=course_list, years=session["years"], current_year=session["current_year"])
    else:
        data = request.form["csv"]
        handle_csv(data)
        return "OK"


def get_google_provider_cfg():
    return requests.get(app.config["GOOGLE_DISCOVERY_URL"]).json()

@app.route("/oauth", methods=["GET"])
def oauth():
    google_provider_cfg = get_google_provider_cfg()
    auth_endpoint = google_provider_cfg["authorization_endpoint"]
    
    request_uri = google_client.prepare_request_uri(
        auth_endpoint,
        redirect_uri = request.base_url + "/callback",
        scope = ["email"]
    )

    return redirect(request_uri)


@app.route("/oauth/callback", methods=["GET"])
def callback():
    if request.args.get("error") is not None:
        return redirect("/signin")

    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = google_client.prepare_token_request(
        token_endpoint,
        authorization_response = request.url,
        redirect_url = request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers = headers,
        data = body,
        auth = (app.config["GOOGLE_CLIENT_ID"], app.config["GOOGLE_CLIENT_SECRET"])
    )
    google_client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = google_client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(
        uri,
        headers = headers,
        data = body
    )
    sub = userinfo_response.json()["sub"]
    email = userinfo_response.json()["email"]

    user = User.query.filter(User.email == email).first()
    if user is None:
        user = User(email, "")
        db.session.add(user)
        db.session.commit()
        google = GoogleID(user.id, sub)
        db.session.add(google)
        db.session.commit()
        login_user(user, remember = True)
    else:
        google = GoogleID.query.filter(GoogleID.user == user.id).first()
        if google is None:
            google = GoogleID(user.id, sub)
            db.session.add(google)
            db.session.commit()
            login_user(user, remember = True)
        elif google.sub == sub:
            login_user(user, remember = True)

    return redirect(url_for("index"))


@app.route("/signin", methods=["GET", "POST"])
@unauthorized_handler
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
                remember = True if "remember" in request.form.keys() else False
                login_user(user, remember = remember)
                return redirect(url_for("index"))
        flash("The email and/or password do not match.", "error")
        return redirect(url_for("signin"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if not current_user.is_authenticated:
            return render_template("register.html")
        return redirect(url_for("index"))

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
@login_required
def signout():
    logout_user()
    flash("You have successfully signed out!", "info")
    return redirect(url_for("signin"))


def send_password_reset_email(user):
    token = user.get_token()
    reset_url = url_for("reset_password", token=token, _external=True)
    message = (
        "To reset your password, please click the link below:\n\n"
        f"{reset_url}\n\n"
        "If you did not request a password reset, please ignore this email."
    )
    mail.send_message(
        subject="Password reset request",
        sender="noreply@metugpaclaculator.com",
        recipients=[user.email],
        body=message
    )


@app.route("/recovery_page", methods=["GET", "POST"])
def recovery_page():
    if request.method == "GET":
        return render_template("recovery_page.html")
    else:
        email = request.form["email"]
        user = User.query.filter(User.email == email).first()
        if user is not None:
            send_password_reset_email(user)
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
@login_required
def change_password():
    if current_user.password == "":
        flash("You are signed in via google, cannot change password!", "error")
        return redirect(url_for("index"))

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
@login_required
def change_year(year):
    session["current_year"] = year
    return ""


@app.route("/edit_year/<int:value>", methods=["GET"])
@login_required
def edit_year(value):
    if (session["years"] > 1 or value == 3) and (session["years"] < 12 or value == 1):
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
@login_required
def add_course(season):
    new_course = Course(season, current_user.id)
    db.session.add(new_course)
    db.session.commit()

    return render_template(
        "course.html", 
        course_id=new_course.id, 
        course_name="", 
        course_credit=0, 
        course_grade="XX"
    )


@app.route("/delete_course/<int:cid>", methods=["DELETE"])
@login_required
def delete_course(cid):
    Course.query.filter(Course.id == cid, Course.user == current_user.id).delete()
    db.session.commit()
    return ""


@app.route("/change_course", methods=["POST"])
@login_required
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
@login_required
def get_gpa():
    return calc_GPA(get_list())


@app.route("/get_csv", methods=["get"])
@login_required
def get_csv():
    csv_data = "name,season,credit,grade\n"
    courses = Course.query.filter(Course.user == current_user.id)
    for course in courses:
        csv_data += f"{course.name},{course.season},{course.credit},{course.grade}\n"
    
    response = Response(csv_data, content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=course_data.csv"
    return response


@app.route("/terms_of_service", methods=["get"])
def terms_of_service():
    return render_template("terms_of_service.html")


@app.route("/privacy_policy", methods=["get"])
def privacy_policy():
    return render_template("privacy_policy.html")
