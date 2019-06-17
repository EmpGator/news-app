from flask import render_template, request, make_response
from flask import current_app as app
from .models import db, User
from flask_login import current_user, login_required


import pickle


@app.route('/users')
@login_required
def users():
    """Lists all users"""
    users = User.query.all()
    return render_template('users.html', users=users, title="Show Users")


@app.route('/')
@login_required
def index():
    """Place holder for main page view """
    return render_template('index.html')


"""
Article views under this comment are useless
for realworld usecase
"""
@app.route('/article/<id>', methods=['POST', 'GET'])
@login_required
def article(id=0):
    if current_user.monthly_pay:
        return render_template('article.html', article_id=id)
    else:
        paid_articles = pickle.loads(current_user.paid_articles)
        print(paid_articles)
        if request.url in paid_articles:
            return render_template('article.html', article_id=id)
        else:
            return render_template('blocked_article.html', article_id=id)
    return 'Something went wrong'


@app.route('/paidarticle', methods=['POST'])
@login_required
def paid_article():
    data = request.get_json()
    print(data)
    print(request.url)
    print(current_user)
    paid_articles = pickle.loads(current_user.paid_articles)
    paid_articles.append(data['url'])
    current_user.paid_articles = pickle.dumps(paid_articles)
    db.session.commit()
    resp = make_response('Ok', 200)
    return resp


@app.context_processor
def utility_processor():
    def unpickle(pickled_string):
        return pickle.loads(pickled_string)
    return dict(unpickle=unpickle)
