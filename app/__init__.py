import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config.get("REPORTS_DIR", "reports"), exist_ok=True)

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.students import students_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.api import api_bp
    from app.routes.portal import portal_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(students_bp, url_prefix="/students")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(portal_bp, url_prefix="/portal")

    # Create tables
    with app.app_context():
        # Import models so their tables are registered with SQLAlchemy.
        from app.models import user, student, student_account  # noqa: F401
        db.create_all()

    return app
