from flask import render_template, redirect, url_for, request
from flask import current_app as app
from .models import User, Publisher, Article
from flask_login import login_required, current_user
import feedparser
import json


def fetch_articles():
    # TODO: add articles to news_app.xml
    # TODO: filter 6 articles for each data object

    src = 'app\\static\\news_app.xml'
    feed = feedparser.parse(src)
    data = {'MrData': [], 'TrData': [], 'LtData': []}
    author = 'Turun Sanomat'
    for entry in feed.entries:
        obj = {'img': entry.media_content[0]['url'], 'title': entry.title, 'author': author, 'link': entry.link}
        data['MrData'].append(obj)
        data['TrData'].append(obj)
        data['LtData'].append(obj)
    data = json.dumps(data)
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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    data = fetch_articles()
    return render_template('index.html', data=data)


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Placeholder for logged in main page view
    """
    if current_user.role == 'publisher':
        return redirect(url_for('publisher.analytics'))
    data = fetch_articles()
    print(data)
    return render_template('index.html', data=data)


# TODO: add links to all providers
@app.route('/ts')
@login_required
def ts():
    return redirect('http://127.0.0.1:8000/ts/')


@app.route('/hs')
def hs():
    return redirect('http://127.0.0.1:8000/hs/')

