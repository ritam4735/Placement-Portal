from flask import Blueprint, render_template
from datetime import datetime

from models.models import (
    StudentProfile,
    CompanyProfile,
    PlacementDrive,
    Application,
    Testimonial
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():

    student_count = StudentProfile.query.count()

    company_count = CompanyProfile.query.count()

    drive_count = PlacementDrive.query.count()

    app_count = Application.query.count()

    testimonials = Testimonial.query.filter_by(
        is_approved=True
    ).all()

    return render_template(
        "index.html",

        students=student_count,
        companies=company_count,
        drives=drive_count,
        apps=app_count,

        testimonials=testimonials,

        year=datetime.now().year
    )