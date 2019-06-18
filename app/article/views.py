from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from datetime import date
import pickle


bp = Blueprint('article', __name__)


@bp.route('/article/<id>', methods=['POST', 'GET'])
@login_required
def article(id=0):
    if current_user.monthly_pay and current_user.subscription_end is not None and \
     current_user.subscription_end >= date.today():
        return render_template('article/article.html', article_id=id)
    else:
        paid_articles = pickle.loads(current_user.paid_articles)
        print(paid_articles)
        if request.url in paid_articles:
            return render_template('article/article.html', article_id=id)
        else:
            return render_template('article/blocked_article.html', article_id=id)
    return 'Something went wrong'
