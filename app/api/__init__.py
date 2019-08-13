from flask import Blueprint, make_response, jsonify, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
from flask_restful import Api, Resource
from flask_restful.reqparse import RequestParser
from flask_login import current_user, login_required
from app.db import db
from app.models import Article, Publisher, User, ReadArticleLink
from datetime import date, timedelta
from app.constants import *
import requests
import time


pay_req_parser = RequestParser(bundle_errors=True)
pay_req_parser.add_argument('url', required=True)
pay_req_parser.add_argument('domain', required=True)
pay_req_parser.add_argument('article_price')
pay_req_parser.add_argument('article_name')
pay_req_parser.add_argument('article_desc')
pay_req_parser.add_argument('article_date')
pay_req_parser.add_argument('article_category')

access_req_parser = RequestParser(bundle_errors=True)
access_req_parser.add_argument('url')
access_req_parser.add_argument('domain')
access_req_parser.add_argument('article_name')
access_req_parser.add_argument('article_desc')
access_req_parser.add_argument('article_date')
access_req_parser.add_argument('article_category')


api_bp = Blueprint('api', __name__)
api = Api(api_bp)


def get_article(url, domain=None, art_name='', art_date=date.today(), art_desc='', art_category=None):
    """
    Fetches article from database, if article wasn't found, creates new article object

    :param url: Article url, used to fetch article from database
    :param domain:

    :return: article object
    """
    article = Article.query.filter_by(url=url).first()
    if not article:
        publisher = Publisher.query.filter_by(url=domain).first()
        if not publisher:
            if domain:
                publisher = Publisher(name=domain, url=domain)
                db.session.add(publisher)
                db.session.commit()
            else:
                publisher = Publisher.query.filter_by(name='mock').first()

        article = Article(url=url, publisher=publisher, name=art_name, category=art_category,
                          date=art_date, description=art_desc)

        db.session.add(article)
        db.session.commit()
    return article


def get_authenticated_user(user):
    """
    Get's authenticated user if any

    :param: current_user

    :return: User or None
    """
    if user.is_authenticated:
        return user
    uid = get_jwt_identity()
    if uid:
        return User.query.get(int(uid))


def get_user_info(user):
    if user.subscription_end:
        method = 'Monthly Subscription'
        msg = f'Valid until {user.subscription_end}'
    elif user.prepaid_articles:
        method = 'Package subscription'
        msg = f'{user.prepaid_articles} articles left'
    else:
        method = 'Single payments'
        msg = f'{user.tokens} tokens left'

    data = {
        'access': False,
        'name': user.first_name,
        'method': method,
        'expiration': user.subscription_end,
        'package_left': user.prepaid_articles,
        'tokens_left': user.tokens,
        'message': msg
    }
    return data


def get_article_from_args(args):
    url = args.get('url')
    article = Article.query.filter_by(url=url).first()
    if not article and all(args.values()):
        domain = args.get('domain')
        name = args.get('article_name')
        desc = args.get('article_desc')
        day = args.get('article_date')
        category = args.get('article_category')
        day = date.fromisoformat(day)
        category = Category(category)
        article = get_article(url, domain=domain, art_name=name, art_desc=desc,
                              art_category=category, art_date=day)
    return article


class UserInfo(Resource):
    """
    Test for unified endpoint for article pay, user info and accessdata
    """
    @jwt_optional
    def post(self):
        """
        This sends user information,
        all arguments are optional, but if provided, can be used to tell
        if user has access given article or not.

        request body can be left empty or can contain all relevant article information. If given
        article info, new article will be made and added to database. Example request bodies:


        Request:
            { "url": "http://localhost:8000/ts/article/1" }


        Response:
            {
                "access": false,
                "can_pay": true,
                "name": "Matti",
                "method": "Single payments",
                "expiration": null,
                "package_left": 0,
                "tokens_left": 23,
                "message": "23 Tokens left"
            }


        Request:
            {
                "url": "http://localhost:8000/ts/article/1",
                "domain": "http://localhost:8000/ts/",
                "article_name": "Kahvi on hyvää",
                "article_desc": "Kahvi on hyvää ja terveellistä",
                "article_date": "2019-06-21",
                "article_category": "health"
            }

        Response:
            {
                "access": true,
                "can_pay": true,
                "name": "Matti",
                "method": "Package subscription",
                "expiration": null,
                "package_left": 8,
                "tokens_left": 103,
                "message": "8 prepaid articles left"
            }

        article_date must be format YYYY-MM-DD
        currently valid categories are:
            'politics'
            'sports'
            'economy'
            'technology'
            'health'
            'entertainment'


        :return:
        """
        user = get_authenticated_user(current_user)
        if not user:
            return make_response('bad auth', 403)

        args = access_req_parser.parse_args()
        data = get_user_info(user)
        article = get_article_from_args(args)
        data['can_pay'] = False
        if article:
            data['access'] = user.access_article(article)
        if user.can_pay():
            data['can_pay'] = True
        return jsonify(data)


class PayArticle(Resource):
    """
    testpay
    """
    @jwt_optional
    def post(self):
        """
        Handles attempted payment of article.

        This attempts to pay given in request body. If article does not exist it attempts to create
        new article object and add it to database. It responds with user information and if payment
        was successful. Url and domain are required attributes, but if given article doesnt exist
        payment can't happen so article information should be provided as well. Example
        request/response bodies:

        Request:
            { "url": "http://localhost:8000/ts/article/1", "domain": "http://localhost:8000/ts" }


        Response:
            {
                "payment_successful": true,
                "access": true,
                "name": "Matti",
                "method": "Single payments",
                "expiration": null,
                "package_left": 0,
                "tokens_left": 23,
                "message": "23 Tokens left"
            }


        Request:
            {
                "url": "http://localhost:8000/ts/article/1",
                "domain": "http://localhost:8000/ts/",
                "article_name": "Kahvi on hyvää",
                "article_desc": "Kahvi on hyvää ja terveellistä",
                "article_date": "2019-06-21",
                "article_category": "health",
                "article_price": 2
            }

        Response:
            {
                "payment_successful": true,
                "access": true,
                "name": "Matti",
                "method": "Package subscription",
                "expiration": null,
                "package_left": 8,
                "tokens_left": 103,
                "message": "8 prepaid articles left"
            }


        :return:
        """
        user = get_authenticated_user(current_user)
        if not user:
            return make_response('bad auth', 403)
        args = pay_req_parser.parse_args()
        price = args.get('article_price')
        article = get_article_from_args(args)
        if article and user.can_pay() and user.pay_article(article, price=price):
            data = get_user_info(user)
            data['access'] = True
            data['payment_successful'] = True
        else:
            data = get_user_info(user)
            data['payment_successful'] = False
        return jsonify(data)



class TopUp(Resource):
    """
    top up handler
    """
    @login_required
    def post(self):
        """
        Handles POST request
        Checks chosen package and if amount was given. Adds information to user object
        :return: Redirect to index page
        """
        print(request.form)
        option = PayOptions(request.form.get('pay-method', "0"))
        if option == PayOptions.MONTHLY:
            analytics = Publisher.query.filter_by(name='All').first()
            analytics.revenue += (MONTH_PRICE / 100)
            if current_user.subscription_end is None:
                current_user.subscription_end = date.today() + timedelta(days=SUBS_TIME)
            elif current_user.subscription_end <= date.today():
                current_user.subscription_end = date.today() + timedelta(days=SUBS_TIME)
            else:
                current_user.subscription_end += timedelta(days=SUBS_TIME)
            db.session.commit()
        elif option == PayOptions.PACKAGE:
            current_user.prepaid_articles += BUNDLE_SIZE
            db.session.commit()
        elif option == PayOptions.SINGLE:
            amount = request.form.get('amount')
            try:
                amount = int(amount)
            except Exception as e:
                print(e)
                amount = 0
            current_user.tokens += amount
            db.session.commit()
        else:
            flash('something went wrong processing payment')
        return redirect(url_for('index'))

# above routes should be obsolette
api.add_resource(TopUp, '/api/topup')
# Above should be moved
api.add_resource(PayArticle, '/api/payarticle')
api.add_resource(UserInfo, '/api/userinfo')