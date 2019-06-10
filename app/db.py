from flask import Flask, g, current_app
from flask_sqlalchemy import SQLAlchemy


def get_db():
    if 'db' not in g:
        g.db = SQLAlchemy(current_app)


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
