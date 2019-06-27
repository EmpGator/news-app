from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
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
        except:
            flash('email is taken')
            return redirect(url_for('auth.new_entry'))
        return redirect(url_for('auth.login'))

    return render_template('index.html')


# placeholder
@bp.route('/signin', methods=['GET', 'POST'])
def login():
    """
    Login formstuff
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
    """logout route"""
    logout_user()
    return redirect(url_for('index'))
