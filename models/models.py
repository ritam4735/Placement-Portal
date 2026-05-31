from extensions import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import CheckConstraint


# =========================================================
# USER TABLE
# =========================================================

class User(db.Model, UserMixin):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )
    # admin / student / company

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    is_blocked = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# COURSE TABLE
# =========================================================

class Course(db.Model):

    __tablename__ = "courses"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(50),
        unique=True
    )


# =========================================================
# DEPARTMENT TABLE
# =========================================================

class Department(db.Model):

    __tablename__ = "departments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(50),
        unique=True
    )


# =========================================================
# BATCH TABLE
# =========================================================

class Batch(db.Model):

    __tablename__ = "batches"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    year = db.Column(
        db.Integer
    )


# =========================================================
# SEMESTER TABLE
# =========================================================

class Semester(db.Model):

    __tablename__ = "semesters"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    number = db.Column(
        db.Integer
    )


# =========================================================
# STUDENT PROFILE
# =========================================================

class StudentProfile(db.Model):

    __tablename__ = "student_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    # personal
    full_name = db.Column(db.String(100))

    email = db.Column(
        db.String(100),
        unique=True
    )

    phone = db.Column(db.String(20))

    age = db.Column(db.Integer)

    # academic

    enrollment_no = db.Column(
        db.String(50),
        unique=True
    )

    roll_no = db.Column(db.String(50))

    cgpa = db.Column(db.Float)

    placed = db.Column(
        db.Boolean,
        default=False
    )

    blocked = db.Column(
        db.Boolean,
        default=False
    )

    # foreign keys

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id")
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("batches.id")
    )

    semester_id = db.Column(
        db.Integer,
        db.ForeignKey("semesters.id")
    )

    # relationships

    course = db.relationship("Course")
    department = db.relationship("Department")
    batch = db.relationship("Batch")
    semester = db.relationship("Semester")

    # file

    resume = db.Column(
        db.String(200)
    )


# =========================================================
# COMPANY PROFILE
# =========================================================

class CompanyProfile(db.Model):

    __tablename__ = "company_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    registration_id = db.Column(
        db.String(50),
        unique=True
    )

    company_name = db.Column(
        db.String(150),
        nullable=False
    )

    website = db.Column(db.String(200))

    location = db.Column(db.String(100))

    description = db.Column(db.String(300))

    hr_name = db.Column(db.String(100))

    hr_email = db.Column(
        db.String(100),
        unique=True
    )

    hr_phone = db.Column(db.String(20))

    approved = db.Column(
        db.Boolean,
        default=False
    )

    rejected = db.Column(
        db.Boolean,
        default=False
    )

    blocked = db.Column(
        db.Boolean,
        default=False
    )


# =========================================================
# PLACEMENT DRIVE
# =========================================================

class PlacementDrive(db.Model):

    __tablename__ = "placement_drives"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company_profiles.id")
    )

    job_title = db.Column(
        db.String(100)
    )

    job_description = db.Column(
        db.Text
    )

    eligibility = db.Column(
        db.String(200)
    )

    deadline = db.Column(
        db.Date
    )

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    closed = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# APPLICATION
# =========================================================

class Application(db.Model):

    __tablename__ = "applications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student_profiles.id")
    )

    drive_id = db.Column(
        db.Integer,
        db.ForeignKey("placement_drives.id")
    )

    applied_on = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    status = db.Column(
        db.String(20),
        default="Applied"
    )

    __table_args__ = (

        db.UniqueConstraint(
            "student_id",
            "drive_id",
            name="unique_application"
        ),

    )


class Testimonial(db.Model):

    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    role = db.Column(db.String(20))

    rating = db.Column(db.Integer)

    feedback = db.Column(db.Text)

    testimonial = db.Column(db.Text)

    is_approved = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )