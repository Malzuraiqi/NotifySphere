from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__, template_folder=resource_path("website/templates"), static_folder=resource_path("website/static"))
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise ValueError("No SECRET_KEY set in environment variables")
    app.config['SECRET_KEY'] = secret_key
    
    database_url = os.environ.get('DATABASE_URL', f"sqlite:///{DB_NAME}")
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Task

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        """Load user by ID for Flask-Login"""
        if id is None or id == 'None':
            return None
        return User.query.get(int(id))
    return app

def resource_path(relative_path):
    """Get absolute path to resource"""
    import sys
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)