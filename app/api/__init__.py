from flask import Blueprint, make_response, jsonify, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
from flask_restful import Api, Resource
from flask_restful.reqparse import RequestParser
from flask_login import current_user, login_required
from app.db import db
from app.models import Article, Publisher, User
from datetime import date, timedelta
from app.constants import *
import requests
import time

u_data_req_parser = RequestParser(bundle_errors=True)
u_data_req_parser.add_argument("url", required=True)

pay_req_parser = RequestParser(bundle_errors=True)
pay_req_parser.add_argument("url", required=True)

token_req_parser = RequestParser(bundle_errors=True)
token_req_parser.add_argument('amount', required=True)

access_req_parser = RequestParser(bundle_errors=True)
access_req_parser.add_argument('url')
access_req_parser.add_argument('domain')
access_req_parser.add_argument('pay', type=bool)


api_bp = Blueprint('api', __name__)
api = Api(api_bp)


def validate_txid(txid, price):
    """
    Uses bitcoin api to validate slp transaction,
    checks if correct amount was sent to correct address

    :param txid: transaction id

    :param price: amount of tokens that were supposed to be received

    :return: True if transaction was valid Else False

    """
    print('validate_txid')
    url = 'https://rest.bitcoin.com/v2/slp/txDetails/' + txid
    resp = requests.get(url)
    retries = 5
    output_n = None
    tokens_received = 0
    for i in range(retries):
        if resp.status_code == 200:
            data = resp.json()
            for i in data['vout']:
                slp = i['scriptPubKey'].get('slpAddrs', [])
                if SLP_ADDR in slp:
                    output_n = i['n']
                    break
            if output_n:
                tokens_received = int(data['tokenInfo']['sendOutputs'][output_n])
            if tokens_received >= price:
                print('return true')
                return True
        else:
            print(resp.status_code)
            print(resp.text)
            time.sleep(5)
    print('return false')
    return False


def get_article(url):
    """
    Fetches article from database, if article wasn't found, creates new article object

    :param url: Article url, used to fetch article from database

    :return: article object
    """
    article = Article.query.filter_by(url=url).first()
    if not article:
        split_url = url.split('/')
        pub_name = 'mock'
        art_name = 'placeholder'
        if len(split_url) >= 3:
            if split_url[3] == 'ts':
                pub_name = 'Turun sanomat'
            elif split_url[3] == 'hs':
                pub_name = 'Helsingin sanomat'
            elif split_url[3] == 'ks':
                pub_name = 'Keskisuomalainen'
            elif split_url[3] == 'ss':
                pub_name = 'Savon sanomat'
            elif split_url[3] == 'kl':
                pub_name = 'Kauppalehti'
        # This is kinda bad way to get name for publisher
        # Consider adding domain/base url for published model and
        # Querying publisher directly with that
            art_name = ' '.join(split_url[3:])
            # Ok this makes basically no sense. Either go fetch title or use rss feed generated objects

        publisher = Publisher.query.filter_by(name=pub_name).first()
        from random import randint
        from app.constants import Category
        cat = Category(randint(1, 6))
        article = Article(url=url, publisher=publisher, name=art_name, category=cat)
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




class Userdata(Resource):
    """
    Handles user access data to give url

    """
    @jwt_required
    def post(self):
        """
        Handles post request

        :return: Json formatted data with {"access": bool} format
        """
        uid = get_jwt_identity()
        current_user = User.query.get(int(uid))
        args = u_data_req_parser.parse_args()
        url = args.get('url')
        article = get_article(url)
        analytics = Publisher.query.filter_by(name='All').first()
        if any(url == x.url for x in current_user.articles):
            return jsonify({'access': True})
        elif current_user.subscription_end is not None:
            if current_user.subscription_end >= date.today():
                if article not in current_user.read_articles:
                    current_user.read_articles.append(article)
                    article.hits += 1
                    article.monthly_pay += 1
                    article.publisher.monthly_pay += 1
                    analytics.monthly_pay += 1
                    db.session.commit()
                return jsonify({'access': True})
            else:
                current_user.subscription_end = None
                db.session.commit()
        elif current_user.prepaid_articles > 0:
            current_user.prepaid_articles -= 1
            article.hits += 1
            article.package_pay += 1
            article.publisher.package_pay += 1
            article.publisher.revenue += 1
            analytics.revenue += 1
            analytics.package_pay += 1
            current_user.articles.append(article)
            db.session.commit()
            return jsonify({'access': True})
        return jsonify({'access': False})


class OldPaidArticle(Resource):
    """
    Handles token payment POST requests from publishers
    """
    @jwt_optional
    def post(self):
        """
        Handles post request

        possible optimization: add access and user information to response as well

        :return: Response object with text OK or Not enough Tokens
        """
        local_user = current_user
        if not local_user.is_authenticated:
            uid = get_jwt_identity()
            if uid:
                local_user = User.query.get(int(uid))
            else:
                return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        url = args['url']
        if local_user.tokens > 0:
            analytics = Publisher.query.filter_by(name='All').first()
            article = get_article(url)
            article.hits += 1
            article.single_pay += 1
            article.publisher.single_pay += 1
            article.publisher.revenue += 1
            analytics.revenue += 1
            analytics.single_pay += 1
            local_user.articles.append(article)
            local_user.tokens -= 1
            db.session.commit()
            resp = make_response('Ok', 200)
            return resp
        return make_response('Not enough tokens', 200)


class PaidArticle(Resource):
    """
    Handles token payment POST requests from publishers
    """
    @jwt_optional
    def post(self):
        """
        Handles post request

        possible optimization: add access and user information to response as well

        :return: Response object with text OK or Not enough Tokens
        """
        user = get_authenticated_user(current_user)
        if not user:
            return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        article = get_article(args['url'])
        if user.pay_article('single_pay', article):
            return make_response('Ok', 200)
        return make_response('Not enough tokens', 200)


class Test(Resource):
    """
    Test for unified endpoint for article pay, user info and accessdata
    """
    @jwt_optional
    def post(self):
        """

        :return:
        """
        user = get_authenticated_user(current_user)
        if not user:
            return make_response('bad auth', 403)
        args = access_req_parser.parse_args()
        pay = args.get('pay')
        url = args.get('url')
        article = get_article(url)
        data = {
            'access': False,
            'name': user.first_name,
            'method': None,
            'expiration': user.subscription_end,
            'package_left': user.prepaid_articles,
            'tokens_left': user.tokens,
            'message': 'ok'
        }
        if pay and article:
            if not user.pay_article('single_pay', article):
                data['message'] = 'Payment failed'
        elif article:
            data['access'] = user.access_article(article)
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


class Userinfo(Resource):
    """
    Class that sends relevant information of user
    """
    @jwt_optional
    def post(self):
        """
        Sends relevant user info

        :return: json formatted userdata
        """
        local_user = current_user
        if not local_user.is_authenticated:
            uid = get_jwt_identity()
            if uid:
                local_user = User.query.get(int(uid))
            else:
                return jsonify([])
        if local_user.subscription_end:
            pay = 'monthly subscription'
            value = f'valid until {local_user.subscription_end}'
        elif local_user.prepaid_articles:
            pay = 'Package'
            value = f'{local_user.prepaid_articles} articles left'
        else:
            pay = 'Single payments'
            value = f'{local_user.tokens} tokens left'
        data = {'name': local_user.first_name, 'payment_type': pay, 'value': value}
        return jsonify(data)

api.add_resource(Userdata, '/api/userdata')
api.add_resource(PaidArticle, '/api/articlepaid')
api.add_resource(TopUp, '/api/topup')
api.add_resource(Userinfo, '/api/userinfo')
api.add_resource(Test, '/api/test')