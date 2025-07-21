from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

from routes.views import views  # ✅ Import blueprint
from models import db

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "supersecret"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mvr.db"
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "views.login"
login_manager.init_app(app)

# ✅ Đăng ký blueprint
app.register_blueprint(views)

from user import AdminUser

@login_manager.user_loader
def load_user(user_id):
    return AdminUser()
    
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
