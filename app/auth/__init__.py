from flask_login import LoginManager
from app.models import User
from .views import bp
from passlib.hash import pbkdf2_sha256
import base64

login_manager = LoginManager()
auth_bp = bp


@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


# TODO: Check for jwt authorization token
@login_manager.request_loader
def request_loader(request):
    key = request.headers.get('Authorization')
    try:
        email, password = base64.b64decode(key.split(' ')[1]).decode('utf-8').split(':')
        print(email)
        print(password)
        user = User.query.filter_by(email=email).first()
        if user is not None:
            return user
        if user is not None and pbkdf2_sha256.verify(password, user.password):
            return user
    except Exception as e:
        print(e)
    return None
