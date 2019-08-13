import os
from datetime import timedelta


class Config:
    """Set Flask configuration vars."""

    # General Config
    TESTING = True
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')

    # Upload options
    UPLOAD_FOLDER = os.path.join('..', 'instance')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    try:
        os.stat('instance')
    except FileNotFoundError:
        os.mkdir('instance')
    try:
        os.stat(os.path.join('app', 'static', 'profile_pics'))
    except FileNotFoundError:
        os.mkdir(os.path.join('app', 'static', 'profile_pics'))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../instance/test.db'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=365)

    # Mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465 #  587 for TLS 465 for SSl
    MAIL_USERNAME = 'tridample@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    DEFAULT_MAIL_SENDER = 'tridample@gmail.com'
