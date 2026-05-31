from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import re

from extensions import db

# import models
from models.models import (
    User,
    StudentProfile,
    CompanyProfile,
    Course,
    Department,
    Batch,
    Semester
)


# =========================================================
# Blueprint
# =========================================================

auth_bp = Blueprint("auth", __name__)


# =========================================================
# LOGIN
# =========================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # find user
        user = User.query.filter_by(
            username=username
        ).first()

        # check password hash
        if user and check_password_hash(
            user.password,
            password
        ):

            # check is_blocked flag on user row
            if user.is_blocked:
                flash("Your account has been blocked. Contact admin.")
                return redirect("/login")

            # role-specific checks
            if user.role == "company":
                profile = CompanyProfile.query.filter_by(user_id=user.id).first()
                if not profile or not profile.approved:
                    flash("Account pending approval.")
                    return redirect("/login")
                if profile.blocked:
                    flash("Your company account has been blocked. Contact admin.")
                    return redirect("/login")

            if user.role == "student":
                profile = StudentProfile.query.filter_by(user_id=user.id).first()
                if profile and profile.blocked:
                    flash("Your student account has been blocked. Contact admin.")
                    return redirect("/login")

            login_user(user)

            # redirect based on role
            if user.role == "admin":
                return redirect("/admin")

            if user.role == "student":
                return redirect("/student")

            if user.role == "company":
                return redirect("/company")

        else:
            flash("Invalid username or password")

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("main.index"))


# =========================================================
# STUDENT REGISTER
# =========================================================

@auth_bp.route("/register_student", methods=["GET", "POST"])
def register_student():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        age = request.form.get("age")

        roll_no = request.form.get("roll_no")
        cgpa = request.form.get("cgpa")

        course_id = request.form.get("course")
        department_id = request.form.get("department")
        batch_id = request.form.get("batch")
        semester_id = request.form.get("semester")

        # --------------------
        # Required check
        # --------------------

        if not username or not password or not email:
            flash("Required fields missing")
            return redirect("/register_student")

        # --------------------
        # password match
        # --------------------

        if password != confirm:
            flash("Passwords do not match")
            return redirect("/register_student")

        # --------------------
        # username unique
        # --------------------

        if User.query.filter_by(
            username=username
        ).first():

            flash("Username already exists")
            return redirect("/register_student")

        # --------------------
        # email unique
        # --------------------

        if StudentProfile.query.filter_by(
            email=email
        ).first():

            flash("Email already used")
            return redirect("/register_student")

        # --------------------
        # email format
        # --------------------

        pattern = r"^[^@]+@[^@]+\.[^@]+$"

        if not re.match(pattern, email):
            flash("Invalid email")
            return redirect("/register_student")

        # --------------------
        # phone check
        # --------------------

        if not phone.isdigit() or len(phone) != 10:
            flash("Invalid phone")
            return redirect("/register_student")

        # --------------------
        # age check
        # --------------------

        try:
            age = int(age)
        except:
            flash("Invalid age")
            return redirect("/register_student")

        if age < 16 or age > 60:
            flash("Invalid age range")
            return redirect("/register_student")

        # --------------------
        # create user
        # --------------------

        hashed = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed,
            role="student"
        )

        db.session.add(user)
        db.session.commit()

        # --------------------
        # auto enrollment no
        # --------------------

        import uuid
        enrollment_no = "ENR" + str(uuid.uuid4().hex[:8]).upper()

        # --------------------
        # create profile
        # --------------------

        profile = StudentProfile(

            user_id=user.id,

            full_name=name,
            email=email,
            phone=phone,
            age=age,

            enrollment_no=enrollment_no,
            roll_no=roll_no,
            cgpa=cgpa,

            course_id=course_id,
            department_id=department_id,
            batch_id=batch_id,
            semester_id=semester_id
        )

        db.session.add(profile)
        db.session.commit()

        flash("Student registered")

        return redirect("/login")

    # GET request

    courses = Course.query.all()
    departments = Department.query.all()
    batches = Batch.query.all()
    semesters = Semester.query.all()

    return render_template(
        "register_student.html",
        courses=courses,
        departments=departments,
        batches=batches,
        semesters=semesters
    )


# =========================================================
# COMPANY REGISTER
# =========================================================

@auth_bp.route("/register_company", methods=["GET", "POST"])
def register_company():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        company_name = request.form.get("company_name")
        website = request.form.get("website")
        location = request.form.get("location")
        description = request.form.get("description")

        hr_name = request.form.get("hr_name")
        hr_email = request.form.get("hr_email")
        hr_phone = request.form.get("hr_phone")

        # required check

        if not username or not password or not company_name:
            flash("Required fields missing")
            return redirect("/register_company")

        # username unique

        if User.query.filter_by(
            username=username
        ).first():

            flash("Username exists")
            return redirect("/register_company")

        # email unique

        if CompanyProfile.query.filter_by(
            hr_email=hr_email
        ).first():

            flash("Email exists")
            return redirect("/register_company")

        # email format check
        pattern = r"^[^@]+@[^@]+\.[^@]+$"
        if not re.match(pattern, hr_email):
            flash("Invalid HR email format")
            return redirect("/register_company")

        # phone check
        if not hr_phone.isdigit() or len(hr_phone) != 10:
            flash("Invalid phone")
            return redirect("/register_company")

        # create user

        user = User(
            username=username,
            password=generate_password_hash(password),
            role="company"
        )

        db.session.add(user)
        db.session.commit()

        # create profile

        profile = CompanyProfile(

            user_id=user.id,

            company_name=company_name,
            website=website,
            location=location,
            description=description,

            hr_name=hr_name,
            hr_email=hr_email,
            hr_phone=hr_phone,

            approved=False,
            rejected=False,
            blocked=False
        )

        db.session.add(profile)
        db.session.commit()

        flash("Company registered, wait for approval")

        return redirect("/login")

    return render_template("register_company.html")