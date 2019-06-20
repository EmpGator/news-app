import os


class Config:
    """Set Flask configuration vars."""

    # General Config
    TESTING = True
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')

    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    try:
        os.stat('instance')
    except:
        os.mkdir('instance')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../instance/test.db'
