from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from app.db import db
from .forms import NewUserForm, LoginForm
from passlib.hash import pbkdf2_sha256
import pickle


bp = Blueprint('auth', __name__)


@bp.route('/new', methods=['GET', 'POST'])
def new_entry():
    """Endpoint to create a user."""
    form = NewUserForm()
    if form.validate_on_submit():
        print('form validated')
        try:
            articles = []
            articles = pickle.dumps(articles)
            username = form.name.data
            email = form.email.data
            password_hash = pbkdf2_sha256.hash(form.password.data)
            monthly_pay = form.payment_method.data
            new_user = User(username=username, email=email,
                            paid_articles=articles, password=password_hash,
                            monthly_pay=monthly_pay)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(e)
            return render_template('auth/new_user.html', form=form)
    else:
        for item in form.errors.items():
            flash(item)

    return render_template('auth/new_user.html', form=form)


# placeholder
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is not None and pbkdf2_sha256.verify(form.password.data, user.password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """logoutroute"""
    logout_user()
    return redirect(url_for('auth.login'))
