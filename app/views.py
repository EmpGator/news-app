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
    """
    Fetches articles from database and adds them obj that is rendered then in frontpage

    :return: Json formatted article data

    """
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
    """
    Fetches articles from rss feed
    TODO: make this background task to be executed one in a while

    :return: Response: OK, 200
    """
    url_list = [f'http://{PUBLISHER_DOMAIN}/{i}/rss' for i in ['ts', 'hs', 'ks', 'kl', 'ss']]
    import requests
    for src in url_list:
        feed = feedparser.parse(src)
        url = feed.feed.link.replace('http://', '')
        author = Publisher.query.filter_by(url=url).first()
        if author:
            for i, entry in enumerate(feed.entries):
                url = entry.link
                if not Article.query.filter_by(url=url).first():
                    img = entry.media_content[0]['url']
                    if not img:
                        img = author.image
                    article = Article(name=entry.title, publisher=author, image=img, url=url)
                    db.session.add(article)
                    db.session.commit()
            print(f'fetched {author.url} articles succesfully')
        else:
            print('Couldnt find author with given url')
            print(f'URL:\n{url}')
            print('\n'*3)
            publishers = [i.url for i in Publisher.query.all()]
            for i in publishers:
                print(i)
            print('\n'*3)
    return make_response('ok', 200)


@app.route('/')
def index():
    """
    Main page view for non logged in users

    :return: index.html with article data
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    data = get_articles()
    return render_template('index.html', data=data)


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Main page view for logged in users

    :return: index.html with article data
    """
    if current_user.role == Role.PUBLISHER:
        return redirect(url_for('publisher.analytics'))
    data = get_articles()
    return render_template('index.html', data=data)


@app.route('/setcookie')
def setcookie():
    """
    This is mainly for testing purposes
    This attempts to set jwt token cookie at PUBLISHER_DOMAIN

    :return: Response 200
    """
    jwt = create_access_token(identity=current_user.id)
    resp = make_response(f'<img src="http://{PUBLISHER_DOMAIN}/setcookie/{jwt}" >', 200)
    return resp


@app.route('/<site>')
def test(site=''):
    """
    This function redirects user to mocksite
    This is for sidebars

    :param site:
        site name as string

    :return: redirect to {PUBLISHER_DOMAIN}/{site}
    """
    if site not in ['ts', 'hs', 'ks', 'kl', 'ss']:
        return make_response('not found', 404)
    url = f'http://{PUBLISHER_DOMAIN}/{site}'
    return redirect(url)
