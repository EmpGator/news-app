from . import db, login_manager
from flask_login import UserMixin


class User(UserMixin, db.Model):
    """User account database model"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(64), index=False,
                         unique=True, nullable=False)
    email = db.Column(db.String(80), index=True, unique=True,
                      nullable=False)
    paid_articles = db.Column(db.PickleType, nullable=False)
    # There prolly is better way than 2 booleans for this
    # For example setting subscription end date to null
    # Could indicate that payment type is pay-per-article
    # But this will do for now
    monthly_pay = db.Column(db.Boolean, nullable=False)
    subscription_end = db.Column(db.DateTime)
    # TODO: store keys of paid Articles
    #
    # This doesn't work, should use many-to-many relationship
    # or just pickle list of Article id's and use that list to
    # query for paid articles
    # paid_articles = db.relationship('Article', backref=db.backref('users', lazy=True))

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Article(db.Model):
    """Article database model to store payed articles"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)


@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


@login_manager.request_loader
def request_loader(request):
    return None
