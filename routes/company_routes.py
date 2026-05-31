from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db

from models.models import (
    CompanyProfile,
    PlacementDrive,
    Application,
    StudentProfile
)

from datetime import datetime


company_bp = Blueprint("company", __name__)


# =========================================================
# Helper → company check
# =========================================================

def company_only():
    return current_user.role == "company"


# =========================================================
# Company dashboard
# =========================================================

@company_bp.route("/company")
@login_required
def company_dashboard():

    if not company_only():
        abort(403)

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return "Profile not found"

    # all drives of this company
    drives = PlacementDrive.query.filter_by(
        company_id=profile.id
    ).all()

    drive_count = len(drives)

    # all applications of this company
    apps = Application.query.join(
        PlacementDrive,
        Application.drive_id == PlacementDrive.id
    ).filter(
        PlacementDrive.company_id == profile.id
    ).all()

    total_apps = len(apps)

    selected = len(
        [a for a in apps if a.status == "Selected"]
    )

    recent = apps[:5]

    return render_template(
        "company/dashboard.html",
        drives=drives,
        drive_count=drive_count,
        total_apps=total_apps,
        selected=selected,
        recent=recent
    )


# =========================================================
# Create drive
# =========================================================

@company_bp.route("/company/create_drive", methods=["GET", "POST"])
@login_required
def create_drive():

    if not company_only():
        abort(403)

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return "Profile not found"

    # must be approved
    if not profile.approved:
        return "Company not approved"

    # blocked check
    if profile.blocked:
        return "Company blocked"

    if request.method == "POST":

        title = request.form.get("title")
        desc = request.form.get("desc")
        eligibility = request.form.get("eligibility")
        deadline_str = request.form.get("deadline")

        if not title or not deadline_str:
            flash("Title and deadline required")
            return redirect("/company/create_drive")

        # convert to date
        try:
            deadline = datetime.strptime(
                deadline_str,
                "%Y-%m-%d"
            ).date()
        except:
            flash("Invalid date")
            return redirect("/company/create_drive")

        # deadline validation
        if deadline < datetime.utcnow().date():
            flash("Deadline cannot be past")
            return redirect("/company/create_drive")

        drive = PlacementDrive(
            company_id=profile.id,
            job_title=title,
            job_description=desc,
            eligibility=eligibility,
            deadline=deadline,
            status="Pending",
            closed=False
        )

        db.session.add(drive)
        db.session.commit()

        flash("Drive created")

        return redirect("/company")

    return render_template(
        "company/create_drive.html"
    )


# =========================================================
# View applications of drive
# =========================================================

@company_bp.route("/company/applications/<int:drive_id>")
@login_required
def view_applications(drive_id):

    if not company_only():
        abort(403)

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    drive = PlacementDrive.query.get_or_404(
        drive_id
    )

    # ownership check
    if drive.company_id != profile.id:
        return "Not allowed"

    apps = Application.query.filter_by(
        drive_id=drive_id
    ).all()

    data = []

    for a in apps:

        student = StudentProfile.query.get(
            a.student_id
        )

        data.append({
            "app": a,
            "student": student
        })

    return render_template(
        "company/applications.html",
        data=data,
        drive=drive
    )


# =========================================================
# Shortlist student
# =========================================================

@company_bp.route("/company/shortlist/<int:id>", methods=["POST"])
@login_required
def shortlist(id):

    if not company_only():
        abort(403)

    app = Application.query.get_or_404(id)

    drive = PlacementDrive.query.get(
        app.drive_id
    )

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    # ownership check
    if drive.company_id != profile.id:
        return "Not allowed"

    app.status = "Shortlisted"

    db.session.commit()

    return redirect(request.referrer)


# =========================================================
# Reject student
# =========================================================

@company_bp.route("/company/reject/<int:id>", methods=["POST"])
@login_required
def reject(id):

    if not company_only():
        abort(403)

    app = Application.query.get_or_404(id)

    drive = PlacementDrive.query.get(
        app.drive_id
    )

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if drive.company_id != profile.id:
        return "Not allowed"

    app.status = "Rejected"

    db.session.commit()

    return redirect(request.referrer)


# =========================================================
# Select student
# =========================================================

@company_bp.route("/company/select/<int:id>", methods=["POST"])
@login_required
def select(id):

    if not company_only():
        abort(403)

    app = Application.query.get_or_404(id)

    drive = PlacementDrive.query.get(
        app.drive_id
    )

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if drive.company_id != profile.id:
        return "Not allowed"

    app.status = "Selected"

    # mark student as placed
    student = StudentProfile.query.get(app.student_id)
    if student:
        student.placed = True

    db.session.commit()

    return redirect(request.referrer)


# =========================================================
# Edit drive
# =========================================================

@company_bp.route("/company/edit_drive/<int:id>", methods=["GET", "POST"])
@login_required
def edit_drive(id):

    if not company_only():
        abort(403)

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not profile:
        return "Profile not found"

    drive = PlacementDrive.query.get_or_404(id)

    # ownership check
    if drive.company_id != profile.id:
        return "Not allowed"

    # can only edit pending drives
    if drive.status == "Approved":
        flash("Approved drives cannot be edited")
        return redirect("/company")

    if drive.closed:
        flash("Closed drives cannot be edited")
        return redirect("/company")

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        desc = request.form.get("desc", "").strip()
        eligibility = request.form.get("eligibility", "").strip()
        deadline_str = request.form.get("deadline")

        if not title or not deadline_str:
            flash("Title and deadline are required")
            return redirect(f"/company/edit_drive/{id}")

        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format")
            return redirect(f"/company/edit_drive/{id}")

        if deadline < datetime.utcnow().date():
            flash("Deadline cannot be in the past")
            return redirect(f"/company/edit_drive/{id}")

        drive.job_title = title
        drive.job_description = desc
        drive.eligibility = eligibility
        drive.deadline = deadline

        db.session.commit()

        flash("Drive updated successfully")
        return redirect("/company")

    return render_template(
        "company/edit_drive.html",
        drive=drive
    )


# =========================================================
# Close drive
# =========================================================

@company_bp.route("/company/close_drive/<int:id>", methods=["POST"])
@login_required
def close_drive(id):

    if not company_only():
        abort(403)

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    drive = PlacementDrive.query.get_or_404(id)

    if drive.company_id != profile.id:
        return "Not allowed"

    drive.closed = True

    db.session.commit()

    return redirect("/company")

# =========================================================
# DELETE drive (company)
# =========================================================

@company_bp.route("/company/delete_drive/<int:id>", methods=["POST"])
@login_required
def delete_drive(id):

    if not company_only():
        abort(403)

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    drive = PlacementDrive.query.get_or_404(id)

    if drive.company_id != profile.id:
        abort(403)

    # only pending drives can be deleted
    if drive.status == "Approved":
        flash("Approved drives cannot be deleted. Close the drive instead.")
        return redirect("/company")

    # remove applications first
    Application.query.filter_by(drive_id=drive.id).delete()

    db.session.delete(drive)
    db.session.commit()

    flash("Drive deleted.")

    return redirect("/company")


# =========================================================
# FEEDBACK / TESTIMONIAL (company submit)
# =========================================================

from models.models import Testimonial


@company_bp.route("/company/feedback", methods=["GET", "POST"])
@login_required
def company_feedback():

    if not company_only():
        abort(403)

    profile = CompanyProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if request.method == "POST":

        ftype    = request.form.get("ftype")      # "feedback" or "testimonial"
        feedback = request.form.get("feedback", "").strip()
        ttext    = request.form.get("testimonial", "").strip()

        try:
            rating = int(request.form.get("rating", 5))
            rating = max(1, min(5, rating))
        except ValueError:
            rating = 5

        if not feedback and not ttext:
            flash("Please fill in at least one field.")
            return redirect("/company/feedback")

        entry = Testimonial(
            user_id=current_user.id,
            role="company",
            rating=rating,
            feedback=feedback if feedback else None,
            testimonial=ttext if ttext else None,
            is_approved=False
        )

        db.session.add(entry)
        db.session.commit()

        flash("Thank you! Your submission has been received. Testimonials go live after admin approval.")
        return redirect("/company")

    # GET: load past submissions by this user
    past = Testimonial.query.filter_by(
        user_id=current_user.id,
        role="company"
    ).order_by(Testimonial.created_at.desc()).all()

    return render_template(
        "company/feedback.html",
        past=past
    )
