from flask import Blueprint, make_response
from flask_restful import Api, Resource
from flask_restful.reqparse import RequestParser
from flask_login import current_user
from app.db import db
import pickle
from datetime import date, timedelta

u_data_req_parser = RequestParser(bundle_errors=True)
u_data_req_parser.add_argument("url", required=True)

pay_req_parser = RequestParser(bundle_errors=True)
pay_req_parser.add_argument("url", required=True)
pay_req_parser.add_argument("txid", required=True)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# TODO: split this into two different arg parsers?


class Userdata(Resource):
    # TODO: send better formated info pack:
    # It should not contain all user data, but rather info
    # if given article has been paid or not
    def post(self):
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = u_data_req_parser.parse_args()
        paid_articles = pickle.loads(current_user.paid_articles)
        if args['url'] in paid_articles:
            return {'access': True}
        elif current_user.subscription_end is not None:
            if current_user.subscription_end >= date.today():
                return {'access': True}
            else:
                current_user.subscription_end = None
                db.session.commit()
        return {'access': False}


class PaidArticle(Resource):
    def post(self):
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        if args['txid']:
            paid_articles = pickle.loads(current_user.paid_articles)
            paid_articles.append(args['url'])
            current_user.paid_articles = pickle.dumps(paid_articles)
            db.session.commit()
            resp = make_response('Ok', 200)
            return resp
        return make_response('Invalid txid', 200)


class PaidMonth(Resource):
    def post(self):
        print('PaidMonth')
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = pay_req_parser.parse_args()
        print(args['txid'])
        if args['txid']:
            if current_user.subscription_end is None:
                current_user.subscription_end = date.today() + timedelta(days=30)
            if current_user.subscription_end <= date.today():
                current_user.subscription_end = date.today() + timedelta(days=30)
            else:
                current_user.subscription_end = current_user.subscription_end + timedelta(days=30)
            db.session.commit()
            return make_response('Ok', 200)
        return make_response('Invalid txid', 200)


api.add_resource(Userdata, '/api/userdata')
api.add_resource(PaidArticle, '/api/articlepaid')
api.add_resource(PaidMonth, '/api/monthpaid')
