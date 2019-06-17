from flask import Blueprint
from flask_restful import Api, Resource
from flask_restful.reqparse import RequestParser
from flask_login import login_required, current_user
import pickle

req_parser = RequestParser(bundle_errors=True)
req_parser.add_argument("url", required=True)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)


class Userdata(Resource):
    def get(self):
        return {'hello': 'world'}

    @login_required
    def post(self):
        args = req_parser.parse_args()
        for arg in args:
            print(arg, args[arg])
        user = current_user
        user_data = {'name': user.username, 'email': user.email, 'Paid articles':
                     pickle.loads(user.paid_articles), 'Monthly payment': user.monthly_pay}
        return {'yk': 'ok', 'user': user_data}


api.add_resource(Userdata, '/api/userdata')
