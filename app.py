from flask import Flask, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

from forms import RegistrationForm, LoginForm
from models import db, User, Course, Enrollment

app = Flask(__name__)
app.config["SECRET_KEY"] = "mysecret"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "instance", "enrollment.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("login"))

        hashed_pw = generate_password_hash(form.password.data)
        user = User(email=form.email.data, password_hash=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("No account found. Please register first.", "warning")
            return redirect(url_for("register"))

        if check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            session["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/home")
@login_required
def home():
    return render_template("home.html", last_login=session.get("last_login"))


@app.route("/courses")
@login_required
def courses():
    courses = Course.query.all()
    return render_template("courses.html", courses=courses)


@app.route("/enroll/<int:course_id>")
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)

    existing = Enrollment.query.filter_by(user_id=current_user.id, course_id=course.id).first()
    if existing:
        flash("You are already enrolled in this course.", "info")
    else:
        enrollment = Enrollment(user_id=current_user.id, course_id=course.id)
        db.session.add(enrollment)
        db.session.commit()
        flash(f"You have successfully enrolled in {course.name}.", "success")

    return redirect(url_for("my_enrollments"))


@app.route("/my_enrollments")
@login_required
def my_enrollments():
    enrollments = Enrollment.query.filter_by(user_id=current_user.id).all()
    return render_template("enrollments.html", enrollments=enrollments)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    os.makedirs(os.path.join(basedir, "instance"), exist_ok=True)
    with app.app_context():
        db.create_all()
        if Course.query.count() == 0:
            sample_courses = [
                Course(name="Python Basics", description="Learn Python programming from scratch."),
                Course(name="Flask Web Development", description="Build web apps using Flask."),
                Course(name="Data Science", description="Introduction to Data Science concepts.")
            ]
            db.session.add_all(sample_courses)
            db.session.commit()

    app.run(debug=False)

