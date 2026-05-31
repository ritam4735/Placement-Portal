from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from extensions import db

# import models
from models.models import (
    User,
    CompanyProfile,
    StudentProfile,
    PlacementDrive,
    Application,
    Course,
    Department,
    Batch,
    Semester
)

admin_bp = Blueprint("admin", __name__)


# =========================================================
# Helper → check admin role
# =========================================================

def admin_only():
    return current_user.role == "admin"


# =========================================================
# Dashboard
# =========================================================

@admin_bp.route("/admin")
@login_required
def admin_dashboard():

    if not admin_only():
        abort(403)

    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()

    active_drives = PlacementDrive.query.filter_by(
        status="Approved"
    ).count()

    pending_drives = PlacementDrive.query.filter_by(
        status="Pending"
    ).count()

    placements = Application.query.filter_by(
        status="Selected"
    ).count()

    total_apps = Application.query.count()

    recent_apps = Application.query.order_by(
        Application.applied_on.desc()
    ).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        students=total_students,
        companies=total_companies,
        drives=active_drives,
        pending=pending_drives,
        placements=placements,
        apps=total_apps,
        recent=recent_apps
    )


# =========================================================
# COMPANIES
# search by name / hr / email / phone / location
# =========================================================

@admin_bp.route("/admin/companies")
@login_required
def view_companies():

    if not admin_only():
        abort(403)

    q = request.args.get("q")

    query = CompanyProfile.query

    if q:

        query = query.filter(
            db.or_(
                CompanyProfile.company_name.contains(q),
                CompanyProfile.hr_name.contains(q),
                CompanyProfile.hr_email.contains(q),
                CompanyProfile.hr_phone.contains(q),
                CompanyProfile.location.contains(q)
            )
        )

    companies = query.all()

    return render_template(
        "admin/companies.html",
        companies=companies
    )


# =========================================================
# company detail
# =========================================================

@admin_bp.route("/admin/company/<int:id>")
@login_required
def company_detail(id):

    if not admin_only():
        abort(403)

    company = CompanyProfile.query.get_or_404(id)

    return render_template(
        "admin/company_detail.html",
        company=company
    )


# =========================================================
# approve / reject / block / unblock company
# =========================================================

@admin_bp.route("/admin/approve_company/<int:id>", methods=["POST"])
@login_required
def approve_company(id):

    if not admin_only():
        abort(403)

    company = CompanyProfile.query.get_or_404(id)

    company.approved = True
    company.rejected = False

    db.session.commit()

    return redirect(url_for("admin.view_companies"))


@admin_bp.route("/admin/reject_company/<int:id>", methods=["POST"])
@login_required
def reject_company(id):

    if not admin_only():
        abort(403)

    company = CompanyProfile.query.get_or_404(id)

    company.rejected = True

    db.session.commit()

    return redirect(url_for("admin.view_companies"))


@admin_bp.route("/admin/block_company/<int:id>", methods=["POST"])
@login_required
def block_company(id):

    if not admin_only():
        abort(403)

    company = CompanyProfile.query.get_or_404(id)

    company.blocked = True

    db.session.commit()

    return redirect(url_for("admin.view_companies"))


@admin_bp.route("/admin/unblock_company/<int:id>", methods=["POST"])
@login_required
def unblock_company(id):

    if not admin_only():
        abort(403)

    company = CompanyProfile.query.get_or_404(id)

    company.blocked = False

    db.session.commit()

    return redirect(url_for("admin.view_companies"))


# =========================================================
# STUDENTS
# search + filters
# =========================================================

@admin_bp.route("/admin/students")
@login_required
def view_students():

    if not admin_only():
        abort(403)

    q = request.args.get("q")
    course_id = request.args.get("course")
    dept_id = request.args.get("department")
    batch_id = request.args.get("batch")
    sem_id = request.args.get("semester")
    cgpa = request.args.get("cgpa")

    query = StudentProfile.query

    # -------- search --------

    if q:

        query = query.filter(
            db.or_(
                StudentProfile.full_name.contains(q),
                StudentProfile.email.contains(q),
                StudentProfile.roll_no.contains(q),
                StudentProfile.enrollment_no.contains(q)
            )
        )

    placed = request.args.get("placed")

    # -------- filters --------

    if course_id:
        query = query.filter(
            StudentProfile.course_id == course_id
        )

    if dept_id:
        query = query.filter(
            StudentProfile.department_id == dept_id
        )

    if batch_id:
        query = query.filter(
            StudentProfile.batch_id == batch_id
        )

    if sem_id:
        query = query.filter(
            StudentProfile.semester_id == sem_id
        )

    if cgpa:
        try:
            query = query.filter(
                StudentProfile.cgpa >= float(cgpa)
            )
        except:
            pass

    if placed:
        query = query.filter(
            StudentProfile.placed == True
        )

    students = query.all()

    # send filter lists to template

    courses = Course.query.all()
    departments = Department.query.all()
    batches = Batch.query.all()
    semesters = Semester.query.all()

    return render_template(
        "admin/students.html",
        students=students,
        courses=courses,
        departments=departments,
        batches=batches,
        semesters=semesters
    )


# =========================================================
# Student detail view
# =========================================================

@admin_bp.route("/admin/student/<int:id>")
@login_required
def student_detail(id):

    if not admin_only():
        abort(403)

    student = StudentProfile.query.get_or_404(id)

    apps = Application.query.filter_by(
        student_id=student.id
    ).all()

    drive_map = {}
    for a in apps:
        drive = PlacementDrive.query.get(a.drive_id)
        company = CompanyProfile.query.get(drive.company_id) if drive else None
        drive_map[a.id] = {"drive": drive, "company": company}

    return render_template(
        "admin/student_detail.html",
        student=student,
        apps=apps,
        drive_map=drive_map
    )


# =========================================================
# Edit student (admin)
# =========================================================

@admin_bp.route("/admin/edit_student/<int:id>", methods=["GET", "POST"])
@login_required
def edit_student(id):

    if not admin_only():
        abort(403)

    profile = StudentProfile.query.get_or_404(id)

    courses = Course.query.all()
    departments = Department.query.all()
    batches = Batch.query.all()
    semesters = Semester.query.all()

    if request.method == "POST":

        profile.enrollment_no = request.form.get("enrollment", "").strip()
        profile.roll_no = request.form.get("roll", "").strip()

        try:
            profile.cgpa = float(request.form.get("cgpa", 0))
        except ValueError:
            pass

        profile.course_id = request.form.get("course_id") or None
        profile.department_id = request.form.get("department_id") or None
        profile.batch_id = request.form.get("batch_id") or None
        profile.semester_id = request.form.get("semester_id") or None

        db.session.commit()

        flash("Student updated")
        return redirect(url_for("admin.student_detail", id=id))

    return render_template(
        "admin/edit_student.html",
        profile=profile,
        courses=courses,
        departments=departments,
        batches=batches,
        semesters=semesters
    )


# =========================================================
# block / unblock student
# =========================================================

@admin_bp.route("/admin/block_student/<int:id>", methods=["POST"])
@login_required
def block_student(id):

    if not admin_only():
        abort(403)

    student = StudentProfile.query.get_or_404(id)

    student.blocked = True

    db.session.commit()

    return redirect(url_for("admin.view_students"))


@admin_bp.route("/admin/unblock_student/<int:id>", methods=["POST"])
@login_required
def unblock_student(id):

    if not admin_only():
        abort(403)

    student = StudentProfile.query.get_or_404(id)

    student.blocked = False

    db.session.commit()

    return redirect(url_for("admin.view_students"))


# =========================================================
# DRIVES
# =========================================================

@admin_bp.route("/admin/drives")
@login_required
def view_drives():

    if not admin_only():
        abort(403)

    status_filter = request.args.get("status")

    query = PlacementDrive.query

    if status_filter:
        query = query.filter(PlacementDrive.status == status_filter)

    drives = query.all()

    return render_template(
        "admin/drives.html",
        drives=drives
    )


# =========================================================
# DRIVE APPLICATIONS (admin view)
# =========================================================

@admin_bp.route("/admin/drive/<int:id>")
@login_required
def drive_detail(id):

    if not admin_only():
        abort(403)

    drive = PlacementDrive.query.get_or_404(id)

    apps = Application.query.filter_by(drive_id=id).all()

    data = []

    for a in apps:
        student = StudentProfile.query.get(a.student_id)
        data.append({"app": a, "student": student})

    return render_template(
        "admin/drive_detail.html",
        drive=drive,
        data=data
    )


@admin_bp.route("/admin/approve_drive/<int:id>", methods=["POST"])
@login_required
def approve_drive(id):

    if not admin_only():
        abort(403)

    drive = PlacementDrive.query.get_or_404(id)

    drive.status = "Approved"

    db.session.commit()

    return redirect(url_for("admin.view_drives"))


@admin_bp.route("/admin/reject_drive/<int:id>", methods=["POST"])
@login_required
def reject_drive(id):

    if not admin_only():
        abort(403)

    drive = PlacementDrive.query.get_or_404(id)

    drive.status = "Rejected"

    db.session.commit()

    return redirect(url_for("admin.view_drives"))


# =========================================================
# COURSES
# =========================================================

@admin_bp.route("/admin/courses", methods=["GET", "POST"])
@login_required
def manage_courses():

    if not admin_only():
        abort(403)

    if request.method == "POST":

        name = request.form.get("name")

        if name:
            db.session.add(Course(name=name))
            db.session.commit()

    courses = Course.query.all()

    return render_template(
        "admin/courses.html",
        courses=courses
    )


@admin_bp.route("/admin/delete_course/<int:id>", methods=["POST"])
@login_required
def delete_course(id):

    if not admin_only():
        abort(403)

    c = Course.query.get_or_404(id)

    db.session.delete(c)
    db.session.commit()

    return redirect(url_for("admin.manage_courses"))


# =========================================================
# DEPARTMENTS
# =========================================================

@admin_bp.route("/admin/departments", methods=["GET", "POST"])
@login_required
def manage_departments():

    if not admin_only():
        abort(403)

    if request.method == "POST":

        name = request.form.get("name")

        if name:
            db.session.add(Department(name=name))
            db.session.commit()

    departments = Department.query.all()

    return render_template(
        "admin/departments.html",
        departments=departments
    )


@admin_bp.route("/admin/delete_department/<int:id>", methods=["POST"])
@login_required
def delete_department(id):

    if not admin_only():
        abort(403)

    d = Department.query.get_or_404(id)

    db.session.delete(d)
    db.session.commit()

    return redirect(url_for("admin.manage_departments"))


# =========================================================
# BATCHES
# =========================================================

@admin_bp.route("/admin/batches", methods=["GET", "POST"])
@login_required
def manage_batches():

    if not admin_only():
        abort(403)

    if request.method == "POST":

        year = request.form.get("year")

        if year:
            db.session.add(Batch(year=year))
            db.session.commit()

    batches = Batch.query.all()

    return render_template(
        "admin/batches.html",
        batches=batches
    )


@admin_bp.route("/admin/delete_batch/<int:id>", methods=["POST"])
@login_required
def delete_batch(id):

    if not admin_only():
        abort(403)

    b = Batch.query.get_or_404(id)

    db.session.delete(b)
    db.session.commit()

    return redirect(url_for("admin.manage_batches"))


# =========================================================
# SEMESTERS
# =========================================================

@admin_bp.route("/admin/semesters", methods=["GET", "POST"])
@login_required
def manage_semesters():

    if not admin_only():
        abort(403)

    if request.method == "POST":

        num = request.form.get("number")

        if num:
            db.session.add(Semester(number=num))
            db.session.commit()

    semesters = Semester.query.all()

    return render_template(
        "admin/semesters.html",
        semesters=semesters
    )


@admin_bp.route("/admin/delete_semester/<int:id>", methods=["POST"])
@login_required
def delete_semester(id):

    if not admin_only():
        abort(403)

    s = Semester.query.get_or_404(id)

    db.session.delete(s)
    db.session.commit()

    return redirect(url_for("admin.manage_semesters"))

# =========================================================
# DELETE STUDENT (admin)
# =========================================================

@admin_bp.route("/admin/delete_student/<int:id>", methods=["POST"])
@login_required
def delete_student(id):

    if not admin_only():
        abort(403)

    student = StudentProfile.query.get_or_404(id)

    # remove applications first
    Application.query.filter_by(student_id=student.id).delete()

    # remove user account
    user = User.query.get(student.user_id)

    db.session.delete(student)

    if user:
        db.session.delete(user)

    db.session.commit()

    flash("Student deleted successfully.")

    return redirect(url_for("admin.view_students"))


# =========================================================
# DELETE COMPANY (admin)
# =========================================================

@admin_bp.route("/admin/delete_company/<int:id>", methods=["POST"])
@login_required
def delete_company(id):

    if not admin_only():
        abort(403)

    company = CompanyProfile.query.get_or_404(id)

    # remove all drives and applications belonging to this company
    drives = PlacementDrive.query.filter_by(company_id=company.id).all()

    for d in drives:
        Application.query.filter_by(drive_id=d.id).delete()
        db.session.delete(d)

    user = User.query.get(company.user_id)

    db.session.delete(company)

    if user:
        db.session.delete(user)

    db.session.commit()

    flash("Company deleted successfully.")

    return redirect(url_for("admin.view_companies"))


# =========================================================
# TESTIMONIALS — admin view + approve/delete
# =========================================================

from models.models import Testimonial


@admin_bp.route("/admin/testimonials")
@login_required
def view_testimonials():

    if not admin_only():
        abort(403)

    testimonials = Testimonial.query.order_by(
        Testimonial.created_at.desc()
    ).all()

    return render_template(
        "admin/testimonials.html",
        testimonials=testimonials
    )


@admin_bp.route("/admin/approve_testimonial/<int:id>", methods=["POST"])
@login_required
def approve_testimonial(id):

    if not admin_only():
        abort(403)

    t = Testimonial.query.get_or_404(id)
    t.is_approved = True
    db.session.commit()

    flash("Testimonial approved and published.")

    return redirect(url_for("admin.view_testimonials"))


@admin_bp.route("/admin/reject_testimonial/<int:id>", methods=["POST"])
@login_required
def reject_testimonial(id):

    if not admin_only():
        abort(403)

    t = Testimonial.query.get_or_404(id)
    t.is_approved = False
    db.session.commit()

    flash("Testimonial unpublished.")

    return redirect(url_for("admin.view_testimonials"))


@admin_bp.route("/admin/delete_testimonial/<int:id>", methods=["POST"])
@login_required
def delete_testimonial(id):

    if not admin_only():
        abort(403)

    t = Testimonial.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()

    flash("Testimonial deleted.")

    return redirect(url_for("admin.view_testimonials"))
