from flask import render_template, redirect, url_for, request, make_response
from flask import current_app as app
from flask_jwt_extended import create_access_token
from flask_login import login_required, current_user
from app.constants import PUBLISHER_DOMAIN, Role
import feedparser
import json


def fetch_articles():
    # TODO: move mock rss feed to mocksite
    # TODO: support unique rss from each publisher
    # TODO: fetch publisher from database based on domain/base url
    # TODO: create new or use existing Article objects from rss items
    src = 'app\\static\\news_app.xml'
    feed = feedparser.parse(src)
    data = {'MrData': [], 'TrData': [], 'LtData': []}
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
        obj = {'img': entry.media_content[0]['url'], 'title': entry.title, 'author': author,
               'link': entry.link.replace('localhost:8000', PUBLISHER_DOMAIN)}
        if i < 6:
            data['MrData'].append(obj)
        elif i < 12:
            data['TrData'].append(obj)
        else:
            data['LtData'].append(obj)
    data = json.dumps(data)
    return data


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
    if current_user.role == Role.PUBLISHER:
        return redirect(url_for('publisher.analytics'))
    data = fetch_articles()
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
