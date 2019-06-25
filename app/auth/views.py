from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.db import db
from passlib.hash import pbkdf2_sha256
import pickle


bp = Blueprint('auth', __name__)


@bp.route('/signup', methods=['GET', 'POST'])
def new_entry():
    """
    Endpoint to create a user.
    TODO: some sort of validation for fields
    """
    if request.method == 'POST':
        print(request.form)
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        password_hash = pbkdf2_sha256.hash(request.form.get('password'))
        articles = []
        articles = pickle.dumps(articles)
        new_user = User(first_name=first_name, last_name=last_name, email=email,
                        paid_articles=articles, password=password_hash)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('index.html')


# placeholder
@bp.route('/signin', methods=['GET', 'POST'])
def login():
    """
    Login formstuff
    TODO: some sort of validation for fields
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        print(request.form)
        email = request.form.get('email')
        users = User.query.all()
        for i in users:
            print(i)
        user = User.query.filter_by(email=email).first()
        print(user)
        if user is not None and pbkdf2_sha256.verify(request.form.get('password'), user.password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            print('username or pass incorrect')

    return render_template('index.html')


@bp.route('/logout')
@login_required
def logout():
    """logoutroute"""
    logout_user()
    return redirect(url_for('index'))
