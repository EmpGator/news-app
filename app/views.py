from flask import render_template, redirect, url_for
from flask import current_app as app
from .models import User
from flask_login import login_required, current_user

import json
import pickle


@app.route('/users')
def users():
    """Lists all users"""
    users = User.query.all()
    return render_template('users.html', users=users, title="Show Users")


@app.route('/')
def index():
    """Place holder for main page view """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Placeholder for logged in main page view
    TODO: fetch articles and add them to dashboard
    """
    name = current_user.first_name + ' ' + current_user.last_name
    bought = pickle.loads(current_user.paid_articles)
    end = current_user.subscription_end
    data = {'name': name, 'bought': bought, 'end_date': str(end)}
    data = json.dumps(data)
    return render_template('index.html', data=data)


@app.context_processor
def utility_processor():
    def unpickle(pickled_string):
        return pickle.loads(pickled_string)
    return dict(unpickle=unpickle)
