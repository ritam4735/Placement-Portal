from flask import Flask
from config import Config
from extensions import db, login_manager
from flask import send_from_directory
import os


# import routes
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.student_routes import student_bp
from routes.company_routes import company_bp
from routes.main_routes import main_bp


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(main_bp)


    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):

        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
    )

    return app



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)