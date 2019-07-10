from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager
from .db import db
from .models import init_publishers
from .auth import login_manager, auth_bp
from .api import api_bp
from .user import user_bp
from .publisher import pub_bp

csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
jwt = JWTManager()


def create_app():
    """
    Application factory.

    :return: flask app
    """
    # create app and load config
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    # init flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    csrf.exempt(api_bp)
    jwt.init_app(app)
    # register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(pub_bp)

    # create db, add default accounts
    with app.app_context():
        from . import views
        db.create_all()
        init_publishers()

        return app
