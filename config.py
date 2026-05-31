import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "pp-secret-key-change-in-production-2024"

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "portal.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB

    ALLOWED_EXTENSIONS = {"pdf"}