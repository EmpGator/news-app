from flask import Blueprint, render_template, url_for, redirect, request, jsonify
from flask_login import current_user, login_required
import json

from app import db
from app.csrf import csrf
from app.auth.views import validate_email, validate_name, validate_and_hash_password
from app.models import Article

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
    end = str(current_user.subscription_end) if current_user.subscription_end else None
    paid = current_user.prepaid_articles
    latest = [{'title': i.article.name, 'link': i.article.url, 'accessed': str(i.day)} for i in current_user.read_articles]
    data = {'name': name, 'email': email, 'end_date': end,
            'prepaid': paid, 'tokens': current_user.tokens, 'latestArticles': latest}
    data = json.dumps(data)
    return render_template('index.html', data=data)


@bp.route('/edit', methods=['POST'])
@login_required
def edit():
    """
    Handles edited userdata

    :return:
    """
    first_name = request.form.get('firstName')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password')
    pw_again = request.form.get('password')

    try:
        if first_name:
            validate_name(first_name)
            current_user.first_name = first_name
        if last_name:
            validate_name(last_name)
            current_user.last_name = last_name
        if email:
            validate_email(email)
            current_user.email = email
        if password:
            pw_hash = validate_and_hash_password(password, pw_again)
            current_user.password = pw_hash
        db.session.commit()
    except Exception as e:
        print(e)
    return redirect(url_for('index'))

@bp.route('/payment')
@login_required
def payment():
    return render_template('index.html')


@bp.route('/favtoggle', methods=['POST'])
@csrf.exempt
@login_required
def favtoggle():
    print('test')
    data = request.json
    if not data:
        print('not ok')
        return jsonify(['ei ok'])
    article = Article.query.filter_by(url=data.get('url')).first()
    print('\n'*3)
    if article in current_user.fav_articles:
        print(f'Removing \n{article} \nfrom \n{current_user} \nFavourites')
        print('\n' * 3)
        print('Favourites before: ')
        print(current_user.fav_articles)
        print('\n' * 3)
        current_user.fav_articles.remove(article)
        print('\n' * 3)
        print('Favourites after:')
        print(current_user.fav_articles)
        print('\n' * 3)
    elif article:
        print(f'Adding \n{article} \nto \n{current_user} \nFavourites')
        print('\n' * 3)
        print('Favourites before: ')
        print(current_user.fav_articles)
        print('\n' * 3)
        current_user.fav_articles.append(article)
        print('\n' * 3)
        print('Favourites after:')
        print(current_user.fav_articles)
        print('\n' * 3)
    print('\n' * 3)
    if article:
        db.session.commit()
    return jsonify(['ok'])