from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response, session
from flask_jwt_extended import create_access_token
from flask_login import current_user, login_user, logout_user, login_required

from app.constants import PUBLISHER_DOMAIN
from app.models import User, Article
from app.db import db
from passlib.hash import pbkdf2_sha256
import pickle


bp = Blueprint('auth', __name__)


@bp.route('/signup', methods=['GET', 'POST'])
def new_entry():
    """
    Endpoint to create a user.
    """
    if request.method == 'POST':
        fn = request.form.get('firstName')
        ln = request.form.get('lastName')
        email = request.form.get('email')
        pw_hash = pbkdf2_sha256.hash(request.form.get('password'))
        try:
            # noinspection PyArgumentList
            new_user = User(first_name=fn, last_name=ln, email=email, password=pw_hash, role='user')
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            print(e)
            flash('email is taken')
            return redirect(url_for('auth.new_entry'))
        return redirect(url_for('auth.login'))

    return render_template('index.html')


@bp.route('/signin', methods=['GET', 'POST'])
def login():
    """
    Login form stuff
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user is not None and pbkdf2_sha256.verify(request.form.get('password'), user.password):
            access_token = create_access_token(identity=user.id)
            print(access_token)
            # TODO Encrypt access_token
            login_user(user)
            return render_template('set_cookies.html', domain=PUBLISHER_DOMAIN, token=access_token,
                                   url_to=url_for('dashboard'))
        else:
            print('username or pass incorrect')

    return render_template('index.html')


@bp.route('/logout')
@login_required
def logout():
    """logout route"""
    logout_user()
    return render_template('logout_all.html', domain=PUBLISHER_DOMAIN, url_to=url_for('index'))
