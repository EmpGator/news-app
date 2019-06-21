from .db import db
from flask_login import UserMixin


class User(UserMixin, db.Model):
    """User account database model"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=False, nullable=False)
    email = db.Column(db.String(80), index=True, unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    paid_articles = db.Column(db.PickleType, nullable=False)
    subscription_end = db.Column(db.Date)

    def __repr__(self):
        return f'<User {self.name} {self.email}>'
