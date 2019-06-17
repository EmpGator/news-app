from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.db import db
from .forms import NewUserForm, LoginForm
from passlib.hash import pbkdf2_sha256
import pickle


app = Blueprint('auth', __name__)


@app.route('/new', methods=['GET', 'POST'])
def new_entry():
    """Endpoint to create a user."""
    form = NewUserForm()
    if form.validate_on_submit():
        print('form validated')
        try:
            articles = []
            articles = pickle.dumps(articles)
            username = request.form.get('name')
            email = request.form.get('email')
            password_hash = pbkdf2_sha256.hash(request.form.get('password'))
            new_user = User(username=username, email=email,
                            paid_articles=articles, password=password_hash,
                            monthly_pay=bool(int(request.form.get('payment_method'))))
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(e)
            return render_template('auth/new_user.html', form=form)
    else:
        print(form.errors.items())

    return render_template('auth/new_user.html', form=form)


# placeholder
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print('user is authenticated')
        return redirect(url_for('index'))
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is not None and pbkdf2_sha256.verify(form.password.data, user.password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """logoutroute"""
    logout_user()
    return redirect(url_for('auth.login'))
