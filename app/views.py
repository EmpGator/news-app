from datetime import datetime, date
from time import time

import feedparser
from flask import render_template, redirect, url_for, request, make_response, jsonify
from flask import current_app as app
from flask_jwt_extended import create_access_token
from flask_login import login_required, current_user
from werkzeug.useragents import UserAgent

from app.constants import PUBLISHER_DOMAIN, Role, Category
from app.models import Article, Publisher, Analytics
from app.db import db

import json

# for autodoc
#from flask import Blueprint
#app = Blueprint('asd', __name__)

def get_articles(publishers=None, categories=None):
    """
    Fetches articles from database and adds them obj that is rendered then in frontpage

    :return: article data in python dictionary

    """
    data = []
    for cat in Category:
        articles = Article.query.filter(Article.category == cat)
        art_data_lst = []
        for i, entry in enumerate(articles):
            art_data = get_article_data(entry)
            art_data_lst.append(art_data)
        headline = cat.value
        data.append(dict(name=headline.title(), content=art_data_lst))
    return data

def get_article_data(article):
    """
    Handles single articles data

    :param article:
    :return: dictionary containing article data
    """
    art_data = article.get_data_dict()
    art_data['read'] = False
    art_data['fav'] = False
    if current_user.is_authenticated:

        if any(article == i.article for i in current_user.read_articles):
            art_data['read'] = True
        if article in current_user.fav_articles:
            art_data['fav'] = True
    return art_data


def fetch_articles():
    print('Fetching articles')
    url_list = [(i.rss, i.url) for i in Publisher.query.filter(Publisher.name != 'All')]
    for src, url in url_list:
        print(f'rss: {src}, url: {url}')
        feed = feedparser.parse(src)
        author = Publisher.query.filter_by(url=url).first()
        if author:
            for i, entry in enumerate(feed.entries):
                url = entry.link
                existing_art = Article.query.filter_by(url=url).first()

                try:
                    img = entry.media_content[0]['url']
                except Exception as e:
                    print(e)
                    img = None
                if not img:
                    img = author.image
                try:
                    category = Category(entry.category)
                except Exception as e:
                    category = Category('')
                try:
                    day = date.fromisoformat(entry.published)
                except Exception as e:
                    day = date.today()
                if not existing_art:
                    article = Article(name=entry.title, publisher=author, image=img, url=url,
                                      description=entry.description, date=day, category=category)
                    db.session.add(article)
                    db.session.commit()
                else:
                    existing_art.image = img
                    existing_art.category = category
                    existing_art.date = day
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

@app.route('/fetch_articles')
def fetch_articles_view():
    """
    Fetches articles from rss feed

    :return: Response: OK, 200
    """
    fetch_articles()
    return make_response('ok', 200)


@app.route('/')
def index():
    """
    Main page view for non logged in users

    :return: index.html with article data
    """

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/dashboard')
@login_required
def dashboard():
    """
    Main page view for logged in users

    :return: index.html with article data
    """
    art_data = get_articles()
    if current_user.role == Role.PUBLISHER:
        return redirect(url_for('publisher.analytics'))


    name = current_user.first_name + ' ' + current_user.last_name
    email = current_user.email
    bought = current_user.prepaid_articles
    end = str(current_user.subscription_end) if current_user.subscription_end else None
    paid = current_user.prepaid_articles
    read = [{'title': i.article.name, 'link': i.article.url, 'accessed': str(i.day), 'author': i.article.publisher.name}
            for i in current_user.read_articles if i][:-6:-1]
    favs = [{'title': i.name, 'link': i.url} for i in current_user.fav_articles if i][:-6:-1]
    recent = read + favs
    #from app.models import  PaymentHistory
    #payments = [i.get_dict() for i in PaymentHistory.query.filter_by(user=current_user)]
    user_data = {'name': name, 'email': email, 'bought': bought, 'subscription_end': end, 'favoriteArticles': favs,
                'package_end': paid, 'tokens': current_user.tokens, 'latestArticles': read, 'recentArticles': recent}
    providers = [{'name': provider.name, 'icon': provider.image, 'url': provider.url} for provider in Publisher.query.filter(Publisher.name != 'All')]
    data = {'articles': art_data, 'user': user_data, 'providers': providers}
    data = json.dumps(data)
    return render_template('index.html', data=data)


@app.route('/a')
def analytics():
    # TODO: move this to different module
    ua = UserAgent(request.headers.get('User-Agent'))
    os = ua.platform
    browser = ua.browser + ' ' + ua.version
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    dev = request.args.get('dev')
    dur = request.args.get('dur')
    seconds = request.args.get('time')
    t = datetime.fromtimestamp(int(seconds) / 1e3).time()
    db.session.add(Analytics(device=dev, os=os, browser=browser, duration=dur,
                             traffic=t, lat=lat, lon=lon))
    db.session.commit()
    return make_response('ok')


@app.route('/user_activities')
def user_activities():
    read = [get_article_data(i.article) for i in current_user.read_articles if i]
    favs = [get_article_data(i) for i in current_user.fav_articles if i]
    recent = read + favs
    data = {
                'favoriteArticles': favs,
                'latestArticles': read,
                'recentArticles': recent
            }
    return jsonify(data)


@app.route('/publisher-docs')
def pub_docs():
    return render_template('pub_docs.html')


@app.route('/<site>/')
def redirect_to_mocksites(site=''):
    """
    This function redirects user to mocksite
    This is for sidebars
    # TODO: maybe move away from catch all routes solution

    :param site:
        site name as string

    :return: redirect to {PUBLISHER_DOMAIN}/{site}
    """
    if site not in ['ts', 'hs', 'ks', 'kl', 'ss']:
        return make_response('not found', 404)
    url = f'http://{PUBLISHER_DOMAIN}/{site}'
    return redirect(url)

@app.route('/news')
def redirect_to_news():
    return redirect(f'http://{PUBLISHER_DOMAIN}/news/')

@app.route('/other')
def redirect_to_other():
    return redirect(f'http://{PUBLISHER_DOMAIN}/theothernews')

@app.route('/waldo')
def redirect_to_waldo():
    return redirect(f'http://{PUBLISHER_DOMAIN}/waldonews')
