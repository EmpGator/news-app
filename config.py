import os
from datetime import timedelta


class Config:
    """Set Flask configuration vars."""

    # General Config
    TESTING = False
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    try:
        os.stat('instance')
    except FileNotFoundError:
        os.mkdir('instance')
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