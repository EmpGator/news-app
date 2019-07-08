from flask import render_template, redirect, url_for, request, make_response
from flask import current_app as app
from flask_jwt_extended import create_access_token
from flask_login import login_required, current_user
from app.constants import PUBLISHER_DOMAIN, Role
from app.models import Article, Publisher
from app.db import db
import feedparser
import json


def get_articles():
    data = {'MrData': [], 'TrData': [], 'LtData': []}
    articles = Article.query.filter(Article.image.isnot(None))
    for i, entry in enumerate(articles):
        if i < 6:
            data['MrData'].append(entry.get_data_dict())
        elif i < 12:
            data['TrData'].append(entry.get_data_dict())
        elif i < 18:
            data['LtData'].append(entry.get_data_dict())
        else:
            break
    return json.dumps(data)


@app.route('/fetch_articles')
def fetch_articles():
    # Todo: make this background task
    src = 'app\\static\\news_app.xml'
    feed = feedparser.parse(src)
    # query_publisher_with_this = feed.link
    author = 'mock'
    for i, entry in enumerate(feed.entries):
        if 'hs' in entry.link:
            author = 'Helsingin sanomat'
        elif 'ts' in entry.link:
            author = 'Turun sanomat'
        elif 'ks' in entry.link:
            author = 'Keskisuomalainen'
        elif 'kl' in entry.link:
            author = 'Kauppalehti'
        elif 'ss' in entry.link:
            author = 'Savon sanomat'
        author = Publisher.query.filter_by(name=author).first()
        article = Article(name=entry.title, publisher=author, image=entry.media_content[0]['url'],
                          url=entry.link.replace('localhost:8000', PUBLISHER_DOMAIN))
        db.session.add(article)
        db.session.commit()
    return make_response('ok', 200)


@app.route('/')
def index():
    """Place holder for main page view """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    data = get_articles()
    return render_template('index.html', data=data)


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Placeholder for logged in main page view
    """
    if current_user.role == Role.PUBLISHER:
        return redirect(url_for('publisher.analytics'))
    data = get_articles()
    return render_template('index.html', data=data)


@app.route('/setcookie')
def setcookie():
    jwt = create_access_token(identity=current_user.id)
    resp = make_response(f'<img src="http://{PUBLISHER_DOMAIN}/setcookie/{jwt}" >', 200)
    return resp


@app.route('/<site>')
def test(site=''):
    print(PUBLISHER_DOMAIN)
    url = f'http://{PUBLISHER_DOMAIN}/{site}'
    return redirect(url)
