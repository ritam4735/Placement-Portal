from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    current_app,
    flash,
    abort
)

import os

from flask_login import login_required, current_user

from extensions import db

from werkzeug.utils import secure_filename

from config import Config

from models.models import (
    StudentProfile,
    PlacementDrive,
    Application
)

student_bp = Blueprint("student", __name__)


# =====================================================
# Helper
# =====================================================

def student_only():
    return current_user.role == "student"


# =====================================================
# Dashboard
# =====================================================

@student_bp.route("/student")
@login_required
def student_dashboard():

    if not student_only():
        abort(403)

    profile = StudentProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return "Profile not found"

    if profile.blocked:
        return "Student blocked"

    apps = Application.query.filter_by(
        student_id=profile.id
    ).all()

    total_apps = len(apps)

    shortlisted = len([
        a for a in apps if a.status == "Shortlisted"
    ])

    # only approved + not closed
    drives = PlacementDrive.query.filter_by(
        status="Approved",
        closed=False
    ).all()

    open_drives = len(drives)

    recent = apps[:5]

    return render_template(
        "student/dashboard.html",

        total_apps=total_apps,
        shortlisted=shortlisted,
        open_drives=open_drives,

        drives=drives,
        apps=apps,
        profile=profile,
        recent=recent
    )


# =====================================================
# Apply drive
# =====================================================

@student_bp.route("/apply/<int:id>", methods=["POST"])
@login_required
def apply_drive(id):

    if not student_only():
        abort(403)

    profile = StudentProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return "Profile not found"

    if profile.blocked:
        flash("Blocked")
        return redirect("/student")

    drive = PlacementDrive.query.get_or_404(id)

    # drive checks

    if drive.closed:
        flash("Drive closed")
        return redirect("/student")

    if drive.status != "Approved":
        flash("Drive not approved")
        return redirect("/student")

    existing = Application.query.filter_by(
        student_id=profile.id,
        drive_id=id
    ).first()

    if existing:
        flash("Already applied")
        return redirect("/student")

    app = Application(
        student_id=profile.id,
        drive_id=id
    )

    db.session.add(app)
    db.session.commit()

    flash("Applied successfully")

    return redirect("/student")


# =====================================================
# Resume upload helper
# =====================================================

def allowed_file(filename):

    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower()
        in Config.ALLOWED_EXTENSIONS
    )


# =====================================================
# Upload Resume
# =====================================================

@student_bp.route("/upload_resume", methods=["POST"])
@login_required
def upload_resume():

    if not student_only():
        abort(403)

    file = request.files.get("resume")

    if not file:
        flash("No file selected")
        return redirect("/student")

    if not allowed_file(file.filename):
        flash("Only PDF allowed")
        return redirect("/student")

    # size check (2MB)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)

    if size > 2 * 1024 * 1024:
        flash("File too large")
        return redirect("/student")

    profile = StudentProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return "Profile not found"

    # unique filename
    filename = secure_filename(
        f"{profile.id}_{file.filename}"
    )

    path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(path)

    profile.resume = filename

    db.session.commit()

    flash("Resume uploaded")

    return redirect("/student")


# =====================================================
# Profile
# =====================================================

@student_bp.route("/student/profile", methods=["GET", "POST"])
@login_required
def profile():

    if not student_only():
        abort(403)

    profile = StudentProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return "Profile not found"

    if request.method == "POST":

        new_email = request.form.get("email", "").strip()

        # check email uniqueness (exclude self)
        if new_email and new_email != profile.email:
            taken = StudentProfile.query.filter(
                StudentProfile.email == new_email,
                StudentProfile.id != profile.id
            ).first()
            if taken:
                flash("Email already in use by another student.")
                return redirect("/student/profile")

        profile.full_name = request.form.get("name")
        profile.email = new_email
        profile.phone = request.form.get("phone")
        profile.age = request.form.get("age")

        cgpa_val = request.form.get("cgpa", "").strip()
        if cgpa_val:
            try:
                cgpa_float = float(cgpa_val)
                if 0.0 <= cgpa_float <= 10.0:
                    profile.cgpa = cgpa_float
                else:
                    flash("CGPA must be between 0.0 and 10.0")
                    return redirect("/student/profile")
            except ValueError:
                flash("Invalid CGPA value")
                return redirect("/student/profile")

        db.session.commit()

        flash("Profile updated")

    return render_template(
        "student/profile.html",
        profile=profile
    )

# =====================================================
# FEEDBACK / TESTIMONIAL (student submit)
# =====================================================

from models.models import Testimonial, CompanyProfile


@student_bp.route("/student/feedback", methods=["GET", "POST"])
@login_required
def student_feedback():

    if not student_only():
        abort(403)

    profile = StudentProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return "Profile not found"

    if profile.blocked:
        abort(403)

    if request.method == "POST":

        feedback = request.form.get("feedback", "").strip()
        ttext    = request.form.get("testimonial", "").strip()

        try:
            rating = int(request.form.get("rating", 5))
            rating = max(1, min(5, rating))
        except ValueError:
            rating = 5

        if not feedback and not ttext:
            flash("Please fill in at least one field.")
            return redirect("/student/feedback")

        entry = Testimonial(
            user_id=current_user.id,
            role="student",
            rating=rating,
            feedback=feedback if feedback else None,
            testimonial=ttext if ttext else None,
            is_approved=False
        )

        db.session.add(entry)
        db.session.commit()

        flash("Thank you! Your submission has been received. Testimonials go live after admin approval.")
        return redirect("/student")

    # GET: load past submissions
    past = Testimonial.query.filter_by(
        user_id=current_user.id,
        role="student"
    ).order_by(Testimonial.created_at.desc()).all()

    return render_template(
        "student/feedback.html",
        past=past
    )