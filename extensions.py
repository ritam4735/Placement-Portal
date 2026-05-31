from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

login_manager = LoginManager()

login_manager.login_view = "auth.login"


# ==========================================
# Flask-Login user loader
# tells flask how to load user from DB
# ==========================================

@login_manager.user_loader
def load_user(user_id):

    from models.models import User

    return User.query.get(int(user_id))