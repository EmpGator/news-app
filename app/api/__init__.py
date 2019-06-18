from flask import Blueprint, make_response
from flask_restful import Api, Resource
from flask_restful.reqparse import RequestParser
from flask_login import current_user
from app.db import db
import pickle

req_parser = RequestParser(bundle_errors=True)
req_parser.add_argument("url", required=True)
req_parser.add_argument("txid", required=False)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

# TODO: split this into two different arg parsers?


class Userdata(Resource):
    def get(self):
        return {'hello': 'world'}

    # TODO: send better formated info pack:
    # It should not contain all user data, but rather info
    # if given article has been paid or not
    def post(self):
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = req_parser.parse_args()
        user = current_user
        user_data = {'name': user.username, 'email': user.email, 'Paid articles':
                     pickle.loads(user.paid_articles), 'Monthly payment': user.monthly_pay}
        return {'yk': 'ok', 'user': user_data}


class PaidArticle(Resource):
    def post(self):
        if not current_user.is_authenticated:
            return make_response('Bad username or password', 403)
        args = req_parser.parse_args()
        paid_articles = pickle.loads(current_user.paid_articles)
        paid_articles.append(args['url'])
        current_user.paid_articles = pickle.dumps(paid_articles)
        db.session.commit()
        resp = make_response('Ok', 200)
        return resp


api.add_resource(Userdata, '/api/userdata')
api.add_resource(PaidArticle, '/api/articlepaid')
