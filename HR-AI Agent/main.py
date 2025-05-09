import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from extensions import db, mail, User
from form import main_bp


def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config['PORT'] = os.getenv('PORT')
    app.config['BASE_URL'] = os.getenv('BASE_URL')
    app.config['HOST'] = os.getenv('HOST')

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # mail settings
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # gemini settings
    app.config['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')

    # Initialize the extensions with the app
    db.init_app(app)
    mail.init_app(app)

    # Flask-Login initialization
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # user_loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    return app

