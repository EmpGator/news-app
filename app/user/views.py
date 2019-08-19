import os
from datetime import date, timedelta
from pathlib import Path

from flask import Blueprint, render_template, url_for, redirect, request, jsonify, flash
from flask_login import current_user, login_required
import json

from werkzeug.utils import secure_filename

from app import db
from app.constants import PayOptions, MONTH_PRICE, SUBS_TIME, BUNDLE_SIZE
from app.csrf import csrf
from app.auth.views import validate_email, validate_name, validate_and_hash_password
from app.models import Article, Publisher

"""
Handles user specific views

TODO: add support for account deletion
    One possible way to do this is:
        when user has confirmed email, send delete account confirmation link to email
        if user hasnt confirmed email allow deletion trough edit form without confirmation link 
"""

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
    pic = current_user.image
    if not pic:
        pic = url_for('static', filename='media/profile-placeholder.5a0ca145.png')
    latest = [{'title': i.article.name, 'link': i.article.url, 'accessed': str(i.day)} for i in current_user.read_articles]
    favs = [{'title': i.name, 'link': i.url} for i in current_user.fav_articles]
    data = {'name': name, 'email': email, 'subscription_end': end, 'favoriteArticles': favs, 'image': pic,
            'package_end': paid, 'tokens': current_user.tokens, 'latestArticles': latest[::-1]}
    data = json.dumps({'user': data})
    return render_template('index.html', data=data)


@bp.route('/profileedit', methods=['GET', 'POST'])
@login_required
def edit():
    """
    Handles edited userdata
    TODO: cleanup code here

    :return:
    """
    if request.method != 'POST':
        return render_template('index.html')
    first_name = request.form.get('firstName')
    last_name = request.form.get('lastName')
    email = request.form.get('email')
    password = request.form.get('password')
    pw_again = request.form.get('rPassword')
    prof_pic = request.files.get('photo-file')


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
        if prof_pic:
            ext = Path(prof_pic.filename).suffix
            file_name = f'{current_user.id}{ext}'
            path = os.path.join('app', 'static', 'profile_pics', secure_filename(file_name))
            prof_pic.save(path)
            current_user.image = url_for('static', filename=f'profile_pics/{file_name}')
        db.session.commit()
    except Exception as e:
        print(e)
    return redirect(url_for('index'))

@bp.route('/payment')
@login_required
def payment():
    return render_template('index.html')


@bp.route('/delete')
@bp.route('/delete/<token>')
def delete_account(token=None):
    if current_user.is_authenticated() and not current_user.email_confirmed:
        current_user.delete()
    elif token:
        pass
    else:
        if request.referrer:
            return redirect(url_for(request.referrer))
        return redirect(url_for('dashboard'))
    db.session.commit()
    return redirect(url_for('index'))


@bp.route('/favtoggle', methods=['POST'])
@csrf.exempt
@login_required
def favtoggle():
    data = request.json
    if not data:
        print('not ok')
        return jsonify(['not ok'])
    article = Article.query.filter_by(url=data.get('url')).first()
    if article in current_user.fav_articles:
        current_user.fav_articles.remove(article)
    elif article:
        current_user.fav_articles.append(article)

    if article:
        db.session.commit()
    return jsonify(['ok'])

@bp.route('/topup', methods=['POST'])
@login_required
def TopUp():
    """
    Handles POST request
    Checks chosen package and if amount was given. Adds information to user object
    :return: Redirect to index page
    """
    print(request.form)
    option = PayOptions(request.form.get('pay-method', "0"))
    if option == PayOptions.MONTHLY:
        analytics = Publisher.query.filter_by(name='All').first()
        analytics.revenue += (MONTH_PRICE / 100)
        if current_user.subscription_end is None:
            current_user.subscription_end = date.today() + timedelta(days=SUBS_TIME)
        elif current_user.subscription_end <= date.today():
            current_user.subscription_end = date.today() + timedelta(days=SUBS_TIME)
        else:
            current_user.subscription_end += timedelta(days=SUBS_TIME)
        db.session.commit()
    elif option == PayOptions.PACKAGE:
        current_user.prepaid_articles += BUNDLE_SIZE
        db.session.commit()
    elif option == PayOptions.SINGLE:
        amount = request.form.get('amount')
        try:
            amount = int(amount)
        except Exception as e:
            print(e)
            amount = 0
        current_user.tokens += amount
        db.session.commit()
    else:
        flash('something went wrong processing payment')
    return redirect(url_for('index'))