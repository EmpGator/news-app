from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .db import db
from .auth import login_manager
from .api import api_bp


csrf = CSRFProtect()
login_manager.login_view = 'login'


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    csrf.exempt(api_bp)
    app.register_blueprint(api_bp)
    with app.app_context():
        from . import routes

        db.create_all()

        return app


# TODO: Structure auth to it's own module and blueprint
# TODO: easy way to create and edit accounts + selecting payment
# TODO: Show user tokens
# TODO: Polish external authentication API (JWT tokens)
