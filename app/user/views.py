from flask import Blueprint, render_template, url_for, redirect, request, jsonify
from flask_login import current_user, login_required
import json

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
    bought = [i.url for i in current_user.articles]
    end = str(current_user.subscription_end) if current_user.subscription_end else None
    paid = current_user.prepaid_articles
    data = {'name': name, 'email': email, 'bought': bought, 'end_date': end,
            'prepaid': paid, 'tokens': current_user.tokens}
    data = json.dumps(data)
    return render_template('index.html', data=data)


@bp.route('/edit', methods=['POST'])
@login_required
def edit():
    """
    Handles edited userdata

    :return:
    """
    first_name = request.form.get('first_name')
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

    except Exception as e:
        print(e)

    return redirect(url_for('index'))


bp.route('/favtoggle', methods=['POST'])
@login_required
def favtoggle():
    data = request.json
    article = Article.query.filter_by(url=data.get('url'))
    if article in current_user.favourites:
        current_user.fav_articles.remove(article)
        return jsonify(['ok'])
    elif article:
        current_user.fav_articles.append(article)
    return jsonify(['ok'])