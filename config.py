import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _normalize_db_url(url):
    """Render/Heroku hand out 'postgres://' URLs, but SQLAlchemy needs 'postgresql://'."""
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ML_MODEL_PATH = os.path.join(BASE_DIR, "ml", "models")
    REPORTS_DIR = os.path.join(BASE_DIR, "reports")


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ.get("DATABASE_URL")) or \
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'dev.db')}"


class ProductionConfig(Config):
    DEBUG = False
    # On Render, DATABASE_URL is injected from the linked Postgres instance.
    # Falls back to a local SQLite file so the app still boots if it's unset.
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ.get("DATABASE_URL")) or \
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'prod.db')}"
    # Must be provided in the environment; falls back to the base default otherwise.
    SECRET_KEY = os.environ.get("SECRET_KEY", Config.SECRET_KEY)


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
