from .db import db
from flask_login import UserMixin
from datetime import date
from passlib.hash import pbkdf2_sha256
from .constants import Role, PUBLISHER_DOMAIN, Category

"""
Database models

TODO: add read date to association table to show users when he read article
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
        # TODO: Change this to only check if user already has access to content
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
        # TODO: Change this to 1st attempt monthly payment then package and finally single
        # Method then can be omitted
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
    date = db.Column(db.Date)
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
    image = db.Column(db.String(2000))
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
    from os import path
    names = [('Helsingin sanomat', f'{PUBLISHER_DOMAIN}/hs', path.join('static', 'media', 'Helsinginsanomat.7df10021.svg')),
             ('Turun sanomat', f'{PUBLISHER_DOMAIN}/ts', path.join('static', 'media', 'Turunsanomat.2b59c2f8.svg')),
             ('Savon sanomat', f'{PUBLISHER_DOMAIN}/ss', path.join('static', 'media', 'savonsanomat.d8cb55d7.svg')),
             ('Kauppalehti', f'{PUBLISHER_DOMAIN}/kl', path.join('static', 'media', 'kauppalehti.ec98efbe.svg')),
             ('Keskisuomalainen', f'{PUBLISHER_DOMAIN}/ks', path.join('static', 'media', 'keskisuomalainen.0b4f2b1c.svg')),
             ('mock', f'{PUBLISHER_DOMAIN}/mock', None)]
    publishers = Publisher.query.all()
    if publishers:
        return

    pw_hash = pbkdf2_sha256.hash('test')
    for i, url, img in names:
        pub = Publisher(name=i, url=url, image=img)
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
