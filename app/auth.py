from flask_login import LoginManager
from .models import User
login_manager = LoginManager()


@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


@login_manager.request_loader
def request_loader(request):
    return None
