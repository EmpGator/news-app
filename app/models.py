from .db import db
from flask_login import UserMixin
from datetime import date

# TODO Article table
# TODO Analytics table

association_table = db.Table('association', db.metadata,
    db.Column('left_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('right_id', db.Integer, db.ForeignKey('articles.id'))
)


class User(UserMixin, db.Model):
    """User account database model"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    subscription_end = db.Column(db.Date)
    prepaid_articles = db.Column(db.Integer, default=0, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, user, publisher
    articles = db.relationship('Article', secondary=association_table)

    def __repr__(self):
        return f'User: {self.first_name} {self.last_name} \nemail: {self.email}'

    def check_subscription(self):
        if self.subscription_end is not None:
            if self.subscription_end >= date.today():
                return True
            else:
                self.subscription_end = None
                db.session.commit()
        return False


class Article(db.Model):
    """
    Model to store articles
    """
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2000), unique=True, nullable=False)
    hits = db.Column(db.Integer, nullable=False, default=0)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    publisher = db.relationship('Publisher', back_populates="articles")

    def __repr__(self):
        return f'Article: {self.url} \n by: {self.publisher}'


class Publisher(db.Model):
    """
    Model to store analytics for publishers
    """
    __tablename__ = 'publishers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    revenue = db.Column(db.Integer, nullable=False, default=0)
    monthly_pay = db.Column(db.Integer, nullable=False, default=0)
    package_pay = db.Column(db.Integer, nullable=False, default=0)
    single_pay = db.Column(db.Integer, nullable=False, default=0)
    articles = db.relationship('Article', back_populates="publisher")

    def __repr__(self):
        return f'Publisher: {self.name}'


def init_publishers():
    names = ['Helsingin sanomat', 'Turun sanomat', 'Savon sanomat', 'Kauppalehti',
             'Keskisuomalainen']
    publishers = Publisher.query.all()
    print(publishers)
    if publishers != [] or publishers is not None:
        return

    for i in names:
        pub = Publisher(name=i)
        db.session.add(pub)
    db.session.commit()
