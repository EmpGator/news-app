from flask_login import LoginManager
from app.models import User
from .views import app
from passlib.hash import pbkdf2_sha256
import base64

login_manager = LoginManager()
auth_bp = app


@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


@login_manager.request_loader
def request_loader(request):
    key = request.headers.get('Authorization')
    print(request.headers)
    print(key)
    try:
        username, password = base64.b64decode(key.split(' ')[1]).decode('utf-8').split(':')
        user = User.query.filter_by(username=username).first()
        if user is not None and pbkdf2_sha256.verify(password, user.password):
            print(username)
            print(password)
            return user
    except Exception as e:
        print(e)
    return None
