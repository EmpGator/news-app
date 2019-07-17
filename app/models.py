import json

from .db import db
from flask_login import UserMixin
from datetime import date
from passlib.hash import pbkdf2_sha256
from .constants import Role, PUBLISHER_DOMAIN, Category

"""
Database models
"""

association_table = db.Table('association', db.metadata,
                             db.Column('left_id', db.Integer, db.ForeignKey('users.id')),
                             db.Column('right_id', db.Integer, db.ForeignKey('articles.id'))
                             )


class User(UserMixin, db.Model):
    """
    User account database model
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    password = db.Column(db.String(80), nullable=False)
    subscription_end = db.Column(db.Date)
    prepaid_articles = db.Column(db.Integer, default=0, nullable=False)
    tokens = db.Column(db.Integer, default=0, nullable=False)
    role = db.Column(db.Enum(Role))
    articles = db.relationship('Article', secondary=association_table)
    read_articles = db.relationship('Article', secondary=association_table)
    fav_articles = db.relationship('Article', secondary=association_table)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    publisher = db.relationship('Publisher', back_populates="users")

    def __repr__(self):
        return f'User: {self.first_name} {self.last_name} \nemail: {self.email} \nrole: {self.role}'

    def check_subscription(self):
        """
        Method to check if user has valid monthly subscription
        if subscription has ended it'll be nullified

        :return: True if subscription is valid Else False
        """
        if self.subscription_end is not None:
            if self.subscription_end >= date.today():
                return True
            else:
                self.subscription_end = None
                db.session.commit()
        return False

    def access_article(self, article):
        print(f'Trying to access article\n{article}')
        if article in self.articles:
            return True
        elif self.check_subscription():
            return True
        elif self.prepaid_articles > 0:
            if self.pay_article('package_pay', article):
                return True
        return False


    def pay_article(self, method, article):
        print(f'Pay article: \n Method: {method}\n {article}')
        if method == 'single_pay' and self.tokens > 0:
            if not article.new_paid_article(method):
                return False
            self.tokens -= 1
            self.articles.append(article)
        elif method == 'package_pay' and self.prepaid_articles > 0:
            if not article.new_paid_article(method):
                return False
            self.prepaid_articles -= 1
            self.articles.append(article)
        elif method == 'monthly_pay' and self.check_subscription():
            if not article.new_paid_article(method):
                return False
        else:
            return False
        self.read_articles.append(article)
        db.session.commit()
        return True


class Article(db.Model):
    """
    Model to store articles

    """
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    category = db.Column(db.Enum(Category))
    image = db.Column(db.String(2000))
    url = db.Column(db.String(2000), unique=True, nullable=False)
    hits = db.Column(db.Integer, nullable=False, default=0)
    monthly_pay = db.Column(db.Integer, nullable=False, default=0)
    package_pay = db.Column(db.Integer, nullable=False, default=0)
    single_pay = db.Column(db.Integer, nullable=False, default=0)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    publisher = db.relationship('Publisher', back_populates="articles")

    def __repr__(self):
        return f'Article: {self.url} \n by: {self.publisher}'

    def get_data_dict(self):
        """
        Method that returns relevant article information in python dictionary

        :return: dictionary with keys title, img, author and link
        """
        data = dict(title=self.name, img=self.image, author=self.publisher.name, link=self.url)
        return data

    def new_paid_article(self, method):
        try:
            val = getattr(self, method) + 1
            setattr(self, method, val)
            self.hits += 1
            self.publisher.new_paid_article(method)
            return True
        except AttributeError:
            print(f'Article has no attribute {method}')


class Publisher(db.Model):
    """
    Model to store analytics for publishers
    """
    __tablename__ = 'publishers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    url = db.Column(db.String(2000), unique=True, nullable=False)
    revenue = db.Column(db.Integer, nullable=False, default=0)
    monthly_pay = db.Column(db.Integer, nullable=False, default=0)
    package_pay = db.Column(db.Integer, nullable=False, default=0)
    single_pay = db.Column(db.Integer, nullable=False, default=0)
    articles = db.relationship('Article', back_populates="publisher")
    users = db.relationship('User', back_populates="publisher")

    def __repr__(self):
        return f'Publisher: {self.name}'

    def new_paid_article(self, method):
        try:
            val = getattr(self, method) + 1
            setattr(self, method, val)
            self.revenue += 1
            return True
        except AttributeError:
            print(f'Publisher has no attribute {method}')


def init_publishers():
    """
    This function creates publisher user accounts and adds to db

    :return: None
    """
    names = [('Helsingin sanomat', f'{PUBLISHER_DOMAIN}/hs'), ('Turun sanomat', f'{PUBLISHER_DOMAIN}/ts'),
             ('Savon sanomat', f'{PUBLISHER_DOMAIN}/ss'), ('Kauppalehti', f'{PUBLISHER_DOMAIN}/kl'),
             ('Keskisuomalainen', f'{PUBLISHER_DOMAIN}/ks'), ('mock', f'{PUBLISHER_DOMAIN}/mock')]
    publishers = Publisher.query.all()
    if publishers:
        return

    pw_hash = pbkdf2_sha256.hash('test')
    for i, url in names:
        pub = Publisher(name=i, url=url)
        db.session.add(pub)
        # noinspection PyArgumentList
        user = User(first_name='', last_name='', email=i, password=pw_hash, role=Role.PUBLISHER,
                    publisher=pub)
        db.session.add(user)
    pub = Publisher(name='All', url='admin')
    db.session.add(pub)
    # noinspection PyArgumentList
    user = User(first_name='', last_name='', email='admin', password=pw_hash, role=Role.ADMIN,
                publisher=pub)
    db.session.add(user)
    db.session.commit()
