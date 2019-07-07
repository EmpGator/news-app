from flask import Blueprint, make_response, jsonify, request, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
from flask_restful import Api, Resource
from flask_restful.reqparse import RequestParser
from flask_login import current_user
from app.db import db
from app.models import Article, Publisher, User
from datetime import date, timedelta

import requests
import time

u_data_req_parser = RequestParser(bundle_errors=True)
u_data_req_parser.add_argument("url", required=True)

pay_req_parser = RequestParser(bundle_errors=True)
pay_req_parser.add_argument("url", required=True)
pay_req_parser.add_argument("txid", required=True)

token_req_parser = RequestParser(bundle_errors=True)
token_req_parser.add_argument('amount', required=True)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

SUBS_TIME = 30
BUNDLE_SIZE = 15

SLP_ADDR = 'simpleledger:qq0nu0xa5rxj72wx043ulhm3qs28y95davd6djawyh'
MONTH_PRICE = 1000
BUNDLE_PRICE = 500
SINGLE_PRICE = 100

# TODO make more efficient
# TODO clean up
# TODO authorization to decorator

def validate_txid(txid, price):
    """
    Uses bitcoin api to validate slp transaction,
        checks if correct amount was sent to correct address
    """
    print('validate_txid')
    url = 'https://rest.bitcoin.com/v2/slp/txDetails/' + txid
    resp = requests.get(url)
    retries = 5
    output_n = None
    tokens_recieved = 0
    for i in range(retries):
        if resp.status_code == 200:
            data = resp.json()
            for i in data['vout']:
                slp = i['scriptPubKey'].get('slpAddrs', [])
                if SLP_ADDR in slp:
                    output_n = i['n']
                    break
            if output_n:
                tokens_recieved = int(data['tokenInfo']['sendOutputs'][output_n])
            if tokens_recieved >= price:
                print('return true')
                return True
        else:
            print(resp.status_code)
            print(resp.text)
            time.sleep(5)
    print('return false')
    return False


def get_article(url):
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

            art_name = ' '.join(split_url[2:])

        publisher = Publisher.query.filter_by(name=pub_name).first()
        article = Article(url=url, publisher=publisher, name=art_name)
        db.session.add(article)
        db.session.commit()
    return article


class Userdata(Resource):
    """
    Docstring
    """
    @jwt_required
    def post(self):
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
                article.hits += 1
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
            article.publisher.package_pay += 1
            article.publisher.revenue += 1
            analytics.revenue += 1
            analytics.package_pay += 1
            current_user.articles.append(article)
            db.session.commit()
            return jsonify({'access': True})
        return jsonify({'access': False})


class PaidArticle(Resource):
    """
    Docstring
    """
    @jwt_optional
    def post(self):
        local_user = current_user
        if not local_user.is_authenticated:
            uid = get_jwt_identity()
            if uid:
                local_user = User.query.get(int(uid))
            else:
                return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        txid = args['txid']
        url = args['url']
        if local_user.tokens > 0:
            analytics = Publisher.query.filter_by(name='All').first()
            article = get_article(url)
            article.hits += 1
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


class PaidMonth(Resource):
    """
    Docstring
    """
    @jwt_optional
    def post(self):
        print('PaidMonth')
        local_user = current_user
        if not local_user.is_authenticated:
            uid = get_jwt_identity()
            if uid:
                local_user = User.query.get(int(uid))
            else:
                return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        if args['txid']:
            analytics = Publisher.query.filter_by(name='All').first()
            analytics.revenue += (MONTH_PRICE / 100)
            if local_user.subscription_end is None:
                local_user.subscription_end = date.today() + timedelta(days=SUBS_TIME)
            if local_user.subscription_end <= date.today():
                local_user.subscription_end = date.today() + timedelta(days=SUBS_TIME)
            else:
                local_user.subscription_end += timedelta(days=SUBS_TIME)
            db.session.commit()
            return make_response('Ok', 200)
        return make_response('Invalid txid', 200)


class PaidPackage(Resource):
    """
    Docstring
    """
    @jwt_optional
    def post(self):
        print('PaidPackage')
        local_user = current_user
        if not local_user.is_authenticated:
            uid = get_jwt_identity()
            if uid:
                local_user = User.query.get(int(uid))
            else:
                return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        if args['txid']:
            analytics = Publisher.query.filter_by(name='All').first()
            analytics.revenue += (BUNDLE_PRICE / 100)
            local_user.prepaid_articles += BUNDLE_SIZE
            db.session.commit()
            return make_response('Ok', 200)
        return make_response('Invalid txid', 200)


class PayTokens(Resource):
    """
    test for jwt authorization
    """
    def post(self):
        if not current_user.is_authenticated:
            return make_response('Bad login', 403)


        amount = request.form.get('amount')
        print(request.form)
        try:
            amount = int(amount)
        except Exception as e:
            print(e)
            amount = 0
        print(amount)
        current_user.tokens += amount
        db.session.commit()
        return redirect(url_for('index'))


class Userinfo(Resource):

    @jwt_optional
    def post(self):
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
api.add_resource(PaidPackage, '/api/packagepaid')
api.add_resource(PaidArticle, '/api/articlepaid')
api.add_resource(PaidMonth, '/api/monthpaid')
api.add_resource(PayTokens, '/api/paytokens')
api.add_resource(Userinfo, '/api/userinfo')