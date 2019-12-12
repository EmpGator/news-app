from .db import db
from flask_login import UserMixin
from datetime import date
from passlib.hash import pbkdf2_sha256
from .constants import Role, PUBLISHER_DOMAIN, Category

"""
Database models

TODO: add read date to association table to show users when he read article
"""

user_bought_articles_table = db.Table('user_articles_bought_link', db.metadata,
                                      db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                                      db.Column('article_id', db.Integer, db.ForeignKey('articles.id'))
                                      )

user_read_articles_table = db.Table('user_articles_read_link', db.metadata,
                                    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                                    db.Column('read_article_id', db.Integer, db.ForeignKey('read_articles.id'))
                                    )

user_fav_articles_table = db.Table('user_articles_favourited_link', db.metadata,
                                   db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                                   db.Column('article_id', db.Integer, db.ForeignKey('articles.id'))
                                   )


class ReadArticleLink(db.Model):
    __tablename__ = 'read_articles'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'))
    article = db.relationship('Article', uselist=False)
    day = db.Column(db.Date, nullable=False)


class PaymentHistory(db.Model):
    __tablename__ = 'payment_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', uselist=False)
    amount = db.Column(db.Float, nullable=False)
    day = db.Column(db.Date, nullable=False)
    pay_type = db.Column(db.String(20), nullable=False)

    def get_dict(self):
        return {'date': str(self.day), 'type': self.pay_type, 'value': self.amount}


class User(UserMixin, db.Model):
    """
    User account database model
    TODO: Consider moving read_articles to _read_articles and add property function that gets /
        art_lnks and merges values to single list of article objects with added date field. Setter /
        would then be very simple list that gets given article and makes new art_lnk object out of it
    TODO: add user dict data returning function
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    password = db.Column(db.String(80), nullable=False)
    account_created = db.Column(db.Date)
    image = db.Column(db.String(255))
    subscription_end = db.Column(db.Date)
    prepaid_articles = db.Column(db.Integer, default=0, nullable=False)
    tokens = db.Column(db.Integer, default=0, nullable=False)
    role = db.Column(db.Enum(Role))
    articles = db.relationship('Article', secondary=user_bought_articles_table)
    read_articles = db.relationship('ReadArticleLink', secondary=user_read_articles_table)
    fav_articles = db.relationship('Article', secondary=user_fav_articles_table)
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
        print(f'Trying to access article\n {article}')
        if article in self.articles:
            print('Access granted')
            return True
        print('Access denied')
        return False

    def can_pay(self, price=1):
        if self.check_subscription():
            print('User can pay because of monthly subscription')
            return True
        elif self.prepaid_articles > 0:
            print('User can pay because of prepaid articles')
            return True
        elif self.tokens >= price:
            print('User can pay because of singlepayment tokens')
            return True
        print("User can't pay article")
        return False

    def pay_article(self, article, price=1):
        """

        :param article:
        :return:
        """
        print(f'Pay article: \n {article}\n Price: {price}')
        if article in self.articles:
            print('article has been paid already')
            return True
        if self.check_subscription():
            if not article.new_paid_article('monthly_pay'):
                print('monthly pay failed')
                return False
            print('monthly pay successsfull')
        elif self.prepaid_articles > 0:
            if not article.new_paid_article('package_pay'):
                return False
            self.articles.append(article)
            self.prepaid_articles -= 1

        else:
            if not article.new_paid_article('single_pay'):
                return False
            self.tokens -= 1
            self.articles.append(article)

        if article not in [i.article for i in self.read_articles]:
            article_link = ReadArticleLink(article=article, day=date.today())
            self.read_articles.append(article_link)
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
    description = db.Column(db.String(3000))
    url = db.Column(db.String(2000), unique=True, nullable=False)
    hits = db.Column(db.Integer, nullable=False, default=0)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    monthly_pay = db.Column(db.Integer, nullable=False, default=0)
    package_pay = db.Column(db.Integer, nullable=False, default=0)
    single_pay = db.Column(db.Integer, nullable=False, default=0)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.id'))
    publisher = db.relationship('Publisher', back_populates="articles")

    def __repr__(self):
        return f'Article: {self.url} \n {self.publisher} \n Date: {self.date} \n Category: {self.category} \n Description: {self.description}'

    def get_data_dict(self):
        """
        Method that returns relevant article information in python dictionary

        :return: dictionary with keys title, img, author and link
        """
        data = dict(title=self.name, img=self.image, author=self.publisher.name, link=self.url,
                    preview=self.description, date=str(self.date))
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

    def art_analytics_data(self):
        return {
            'title': self.name,
            'link': self.url,
            'total_reads': self.hits,
            'monthly_percent': round(self.monthly_pay/self.hits*100, 1),
            'package_percent': round(self.package_pay/self.hits*100, 1),
            'single_percent': round(self.single_pay/self.hits*100, 1)
        }


class Publisher(db.Model):
    """
    Model to store publishers data
    TODO: add rss feed link
    """
    __tablename__ = 'publishers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    url = db.Column(db.String(2000), unique=True, nullable=False)
    rss = db.Column(db.String(2000))
    image = db.Column(db.String(2000))
    revenue = db.Column(db.Integer, nullable=False, default=0)
    monthly_pay = db.Column(db.Integer, nullable=False, default=0)
    package_pay = db.Column(db.Integer, nullable=False, default=0)
    single_pay = db.Column(db.Integer, nullable=False, default=0)
    articles = db.relationship('Article', back_populates="publisher")
    users = db.relationship('User', back_populates="publisher")

    def __repr__(self):
        return f'Publisher: {self.name}\n {len(self.articles)} articles\n Admin accounts: {self.users}'

    def new_paid_article(self, method):
        try:
            val = getattr(self, method) + 1
            setattr(self, method, val)
            self.revenue += 1
            return True
        except AttributeError:
            print(f'Publisher has no attribute {method}')


class Analytics(db.Model):
    """
    Model to store common analytics data
    """
    __tablename__ = 'analytics'
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(255))
    os = db.Column(db.String(255))
    browser = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    duration = db.Column(db.Integer)
    traffic = db.Column(db.Time)
    lat = db.Column(db.Integer)
    lon = db.Column(db.Integer)

    def __repr__(self):
        return f'Dev: {self.device}, time: {self.traffic}, dur: {self.duration}'


def init_publishers():
    """
    This function creates publisher user accounts and adds to db


    :return: None
    """
    publishers = Publisher.query.all()
    if publishers:
        return

    """
    from os import path
    
    names = [
        ('Helsingin sanomat', f'{PUBLISHER_DOMAIN}/hs', path.join('static', 'media', 'Helsinginsanomat.7df10021.svg')),
        ('Turun sanomat', f'{PUBLISHER_DOMAIN}/ts', path.join('static', 'media', 'Turunsanomat.2b59c2f8.svg')),
        ('Savon sanomat', f'{PUBLISHER_DOMAIN}/ss', path.join('static', 'media', 'savonsanomat.d8cb55d7.svg')),
        ('Kauppalehti', f'{PUBLISHER_DOMAIN}/kl', path.join('static', 'media', 'kauppalehti.ec98efbe.svg')),
        ('Keskisuomalainen', f'{PUBLISHER_DOMAIN}/ks', path.join('static', 'media', 'keskisuomalainen.0b4f2b1c.svg'))]
    
    pw_hash = pbkdf2_sha256.hash('test')
    for i, url, img in names:
        pub = Publisher(name=i, url=url, image=img, rss=f'http://{url}/rss')
        db.session.add(pub)
        # noinspection PyArgumentList
        user = User(first_name='', last_name='', email=i, password=pw_hash, role=Role.PUBLISHER,
                    publisher=pub)
        db.session.add(user)
    """
    pub = Publisher(name='All', url='admin', rss='admin')
    db.session.add(pub)
    pw_hash = pbkdf2_sha256.hash('test')
    # noinspection PyArgumentList
    user = User(first_name='', last_name='', email='admin', password=pw_hash, role=Role.ADMIN,
                publisher=pub)
    db.session.add(user)
    db.session.commit()
