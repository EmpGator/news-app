from flask import Blueprint, render_template
from flask_login import current_user, login_required
import json

bp = Blueprint('user', __name__)


@bp.route('/profile')
@login_required
def profile():
    """
    Fetches user data that is rendered on profile page

    :return: Profile page with userdata
    """
    name = current_user.first_name + ' ' + current_user.last_name
    email = current_user.email
    bought = [i.url for i in current_user.articles]
    end = str(current_user.subscription_end) if current_user.subscription_end else None
    paid = current_user.prepaid_articles
    data = {'name': name, 'email': email, 'bought': bought, 'end_date': end,
            'prepaid': paid, 'tokens': current_user.tokens}
    data = json.dumps(data)
    return render_template('index.html', data=data)
