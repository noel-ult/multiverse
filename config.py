import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # A predictable session key is never acceptable outside local development.
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY and os.getenv('FLASK_ENV') == 'production':
        raise RuntimeError('SECRET_KEY must be configured in production')
    SECRET_KEY = SECRET_KEY or 'local-development-key-change-me'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///multiverse.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
