from app import create_app
from extensions import db
from models.models import User

from werkzeug.security import generate_password_hash

import os

app = create_app()


with app.app_context():

    db.drop_all()
    db.create_all()

    # ensure uploads folder exists
    uploads_dir = app.config.get("UPLOAD_FOLDER")
    if uploads_dir and not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # create admin user

    admin = User.query.filter_by(
        username="admin"
    ).first()

    if not admin:

        admin = User(
            username="admin",
            password=generate_password_hash("admin"),
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()

    print("Database created")