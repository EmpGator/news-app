from flask import render_template, redirect, url_for, request
from flask import current_app as app
from .models import User, Publisher, Article
from flask_login import login_required, current_user
import feedparser
import json


def fetch_articles():
    src = 'app\\static\\news_app.xml'
    feed = feedparser.parse(src)
    for entry in feed.entries:
        print(entry.title)
        print(entry.media_content[0]['url'])
    data = json.dumps({})
    return data


@app.route('/users')
def users():
    """Lists all users"""
    users = User.query.all()
    pubs = Publisher.query.all()
    arts = Article.query.all()
    return render_template('users.html', users=users, pubs=pubs, arts=arts, title="Show Users")


@app.route('/')
def index():
    """Place holder for main page view """
    print(request.cookies)
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
    if current_user.role == 'publisher':
        return redirect(url_for('publisher.analytics'))
    fetch_articles()
    name = current_user.first_name + ' ' + current_user.last_name
    bought = [i.url for i in current_user.articles]
    end = current_user.subscription_end
    data = {'name': name, 'bought': bought, 'end_date': str(end)}
    data = json.dumps(data)
    return render_template('index.html', data=data)


@app.route('/ts')
@login_required
def ts():
    return render_template('index.html')


@app.route('/hs')
def hs():
    return render_template('index.html')
