from flask import Blueprint, make_response, jsonify
from flask_restful import Api, Resource
from flask_restful.reqparse import RequestParser
from flask_login import current_user
from app.db import db
from app.models import Article, Publisher
from datetime import date, timedelta

import requests
import time

u_data_req_parser = RequestParser(bundle_errors=True)
u_data_req_parser.add_argument("url", required=True)

pay_req_parser = RequestParser(bundle_errors=True)
pay_req_parser.add_argument("url", required=True)
pay_req_parser.add_argument("txid", required=True)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)


SUBS_TIME = 30
BUNDLE_SIZE = 15

SLP_ADDR = 'simpleledger:qq0nu0xa5rxj72wx043ulhm3qs28y95davd6djawyh'
MONTH_PRICE = 1000
BUNDLE_PRICE = 500
SINGLE_PRICE = 100


# TODO split this file logical parts
# TODO store client info
# TODO Clean validate_txid


def validate_txid(txid, price):
    """
    Uses bitcoin api to validate slp transaction,
        checks if correct amount was sent to correct address
    TODO: Check that TXID is new
    TODO: Validate that token is correct type
    """
    print('validate_txid')
    url = 'https://rest.bitcoin.com/v2/slp/txDetails/' + txid
    resp = requests.get(url)
    retries = 5
    for i in range(retries):
        if resp.status_code == 200:
            data = resp.json()
            for i in data['vout']:
                slp = i['scriptPubKey'].get('slpAddrs', [])
                if SLP_ADDR in slp:
                    output_n = i['n']
                    break
            tokens_recieved = data['tokenInfo']['sendOutputs'][output_n]
            if int(tokens_recieved) >= price:
                print('return true')
                return True
        else:
            print(resp.status_code)
            print(resp.text)
            time.sleep(5)
    print('return false')
    return False


def pay_new_article(url):
    article = Article.query.filter_by(url=url).first()
    if not article:
        publisher = Publisher.query.filter_by(name='Turun sanomat').first()
        article = Article(url=url, publisher=publisher)
        db.session.add(article)
    current_user.articles.append(article)
    db.session.commit()


class Userdata(Resource):
    """
    Docstring
    """
    def post(self):
        data = {}
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = u_data_req_parser.parse_args()
        paid_articles = current_user.articles
        url = args.get('url')
        if any(url == x.url for x in current_user.articles):
            return jsonify({'access': True})
        elif current_user.subscription_end is not None:
            if current_user.subscription_end >= date.today():
                return jsonify({'access': True})
            else:
                current_user.subscription_end = None
                db.session.commit()
        if current_user.prepaid_articles > 0:
            current_user.prepaid_articles -= 1
            pay_new_article(url)
            return jsonify({'access': True})
        return jsonify({'access': False})




class PaidArticle(Resource):
    """
    Docstring
    """
    def post(self):
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        txid = args['txid']
        url = args['url']
        if txid:
            pay_new_article(url)
            resp = make_response('Ok', 200)
            return resp
        return make_response('Invalid txid', 200)


class PaidMonth(Resource):
    """
    Docstring
    """
    def post(self):
        print('PaidMonth')
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        if args['txid']:
            if current_user.subscription_end is None:
                current_user.subscription_end = date.today() + timedelta(days=30)
            if current_user.subscription_end <= date.today():
                current_user.subscription_end = date.today() + timedelta(days=30)
            else:
                current_user.subscription_end += timedelta(days=SUBS_TIME)
            db.session.commit()
            return make_response('Ok', 200)
        return make_response('Invalid txid', 200)


class PaidPackage(Resource):
    """
    Docstring
    """
    def post(self):
        print('PaidPackage')
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        if args['txid']:
            current_user.prepaid_articles += BUNDLE_SIZE
            db.session.commit()
            return make_response('Ok', 200)
        return make_response('Invalid txid', 200)


api.add_resource(Userdata, '/api/userdata')
api.add_resource(PaidPackage, '/api/packagepaid')
api.add_resource(PaidArticle, '/api/articlepaid')
api.add_resource(PaidMonth, '/api/monthpaid')
