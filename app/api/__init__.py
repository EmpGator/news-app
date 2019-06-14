from flask import Blueprint
from flask_restful import Api, Resource
from flask_restful.reqparse import RequestParser
from app.models import User
import pickle

req_parser = RequestParser(bundle_errors=True)
req_parser.add_argument("name", type=str, required=True)
req_parser.add_argument("url", required=True)
req_parser.add_argument("password", required=True)

api_bp = Blueprint('api', __name__)
api = Api(api_bp)


class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}

    def post(self):
        args = req_parser.parse_args()
        for arg in args:
            print(arg, args[arg])
        user = User.query.filter(User.username == args['name']).one()
        user_data = {'name': user.username, 'email': user.email, 'Paid articles':
                     pickle.loads(user.paid_articles), 'Monthly payment': user.monthly_pay}
        return {'yk': 'ok', 'user': user_data}


api.add_resource(HelloWorld, '/api/helloworld')
