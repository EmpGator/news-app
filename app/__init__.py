from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager


db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = 'login'


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import routes

        db.create_all()

        return app


# TODO: easy way to create and edit accounts + selecting payment
# TODO: Move auth to blueprint
# TODO: Token buy view
# TODO: User token wallet
# TODO: mock up Authorization of users in news sites
