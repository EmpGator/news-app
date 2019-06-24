from .db import db
from flask_login import UserMixin
from datetime import date


class User(UserMixin, db.Model):
    """User account database model"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), index=False, nullable=False)
    last_name = db.Column(db.String(64), index=False, nullable=False)
    email = db.Column(db.String(80), index=True, unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    paid_articles = db.Column(db.PickleType, nullable=False)
    subscription_end = db.Column(db.Date)
    prepaid_articles = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name} {self.email}>'

    def check_subscription(self):
        if self.subscription_end is not None:
            if self.subscription_end >= date.today():
                return True
            else:
                self.subscription_end = None
                db.session.commit()
        return False
