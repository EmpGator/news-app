from flask import render_template
from flask import current_app as app
from .models import User
from flask_login import login_required


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


@app.context_processor
def utility_processor():
    def unpickle(pickled_string):
        return pickle.loads(pickled_string)
    return dict(unpickle=unpickle)
