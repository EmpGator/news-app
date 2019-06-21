from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .db import db
from .auth import login_manager, auth_bp
from .api import api_bp
from .user import user_bp

csrf = CSRFProtect()
login_manager.login_view = 'auth.login'


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    csrf.exempt(api_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    print(app.url_map)
    with app.app_context():
        from . import views

        db.create_all()

        return app


# TODO: use txid to confirm that payment was correct
# TODO: Monthly payment expiration stuff
# TODO: monthly payment pay
# TODO: api auth JWT tokeneilla
# TODO: easy way to create and edit accounts + selecting payment
# TODO: Show user tokens
