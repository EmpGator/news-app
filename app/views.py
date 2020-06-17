from datetime import datetime, date
from time import time
from bs4 import BeautifulSoup
import feedparser
import requests
from flask import render_template, redirect, url_for, request, make_response, jsonify
from flask import current_app as app
from flask_jwt_extended import create_access_token
from flask_login import login_required, current_user
from sqlalchemy import desc
from werkzeug.useragents import UserAgent

from app.constants import PUBLISHER_DOMAIN, Role, Category
from app.models import Article, Publisher, Analytics
from app.db import db

import json

# for autodoc
#from flask import Blueprint
#app = Blueprint('asd', __name__)
from app.article_parsers import TheVergeParser, EngadgetParser, PoliticoParser, GuardianParser, StuffParser, \
    SpiegelParser, DailyMailParser


def get_articles(publishers=None, categories=None):
    """
    Fetches articles from database and adds them obj that is rendered then in frontpage

    :return: article data in python dictionary

    """
    MAX_PER_PUB = 15
    data = []
    publishers = Publisher.query.order_by('name').all()
    for cat in Category:
        art_data_lst = []
        if cat != Category.OTHER:
            for pub in publishers:
                articles = Article.query.filter(Article.publisher == pub).filter(Article.category == cat).order_by(desc(Article.date)).limit(MAX_PER_PUB)
                for art in articles:
                    art_data_lst.append(get_article_data(art))
        else:
            articles = Article.query.filter(Article.category == cat).order_by(desc(Article.date)).limit(100)
            for art in articles:
                art_data_lst.append(get_article_data(art))

        headline = cat.value
        data.append(dict(name=headline.title(), content=art_data_lst))
        data[0], data[-1] = data[-1], data[0]
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


def generate_article_data(url):
    parser_key_pairs = {
        'guardian': GuardianParser,
        'politico': PoliticoParser,
        'theverge': TheVergeParser,
        'engadget': EngadgetParser,
        'stuff': StuffParser,
        'spiegel': SpiegelParser,
        'dailymail': DailyMailParser,
    }
    for key, parser in  parser_key_pairs.items():
        if key in url.lower():
            return parser(url).get_content()


def fetch_articles():
    print('Fetching articles')
    publishers = Publisher.query.filter(Publisher.name != 'All')
    articles_url_association_dict = {}
    articles = Article.query.all()
    external_publishers = [
        'theguardian',
        'politico',
        'theverge',
        'engadget',
        'stuff',
        'spiegel',
        'sfgate',
        'dailymail'
    ]
    for publisher in publishers:
        src = publisher.rss
        url = publisher.url
        print(f'rss: {src}, url: {url}')
        try:
            r = requests.get(src)
            feed = feedparser.parse(r.text)
        except Exception as e:
            print(f'Exception at 103: {e}')
            continue
        author = publisher
        if author and feed:
            try:
                for i, entry in enumerate(feed.entries):
                    fetch_from_mocksite = False
                    existing = False
                    url = entry.link
                    if any([i in url for i in external_publishers]):
                        articles_url_association_dict[url] = None
                        fetch_from_mocksite = True
                    article = [i for i in articles if i.url == url] or None
                    if article:
                        article = article[0]
                    try:
                        img = entry.media_content[0]['url']
                    except Exception as e:
                        img = None
                    if not img:
                        img = author.image
                    try:
                        terms = []
                        if hasattr(entry, 'tags'):
                            terms = [i.term.lower() for i in entry.tags]
                        category = None
                        for c in Category:
                            cat_name = c.value.lower()
                            if len(cat_name) > 0:
                                cat_name = cat_name[:-1]
                            if cat_name in terms or cat_name in src.lower() or cat_name in url.lower():
                                category = c
                                break
                        if not category:
                            category = Category(entry.category)
                    except Exception as e:
                        category = Category('')
                    try:
                        day = date.fromisoformat(entry.published)
                    except Exception as e:
                        day = date.today()
                    try:
                        desc = BeautifulSoup(entry.description, "lxml").text
                    except:
                        if hasattr(entry, 'description'):
                            desc = entry.description
                            soup = BeautifulSoup(desc, 'html.parser')
                            desc = soup.text.strip()
                            for img in soup.findAll('img'):
                                img = img.get('src')
                                break
                        elif hasattr(entry, 'summary'):
                            desc = entry.summary
                    if not article:
                        article = Article(name=entry.title, publisher=author, image=img, url=url,
                                          description=desc, date=day, category=category)
                    else:
                        existing = True
                        article.image = img if not article.image else article.image
                        article.category = category if category else article.category
                        article.date = day if not article.date else article.date
                        if entry.description:
                            article.description = entry.description
                    if fetch_from_mocksite:
                        articles_url_association_dict[url] = article
                        #generate article here?
                        #gather contents in dict
                    if not existing and not fetch_from_mocksite:
                        db.session.add(article)
                print(f'fetched {author.url} articles succesfully')
            except Exception as e:
                print(f'Exception at 172: {e}')
        else:
            print('Couldnt find author with given url')
            print(f'URL:\n{url}')
            print('\n'*3)
            for i in publishers:
                print(i)
            print('\n'*3)
    try:
        print('Fetching association table')
        payload = {'urls': list(articles_url_association_dict.keys())}
        url = f'http://{PUBLISHER_DOMAIN}/check_urls'
        print('Asking existing article data')
        res = requests.post(url, json=payload) # ask existing article data
        data = res.json()
        mocksite_generate_article_data = []
        print('Fetch not existing articles data')
        for url in data.get('not_existing', []):
            try:
                new_art_data = generate_article_data(url)
            except Exception as e:
                print(f'Exception at 193: {e}')
                new_art_data = None
            if new_art_data:
                header, subheader, avc, roc = new_art_data
                mocksite_generate_article_data.append({
                    'url': url,
                    'header': header,
                    'subheader': subheader,
                    'avc': avc,
                    'roc': roc
                })

        print('Send article generation request')
        mock_generate_art_url = f'http://{PUBLISHER_DOMAIN}/generate_article'
        resp = requests.post(mock_generate_art_url, json=mocksite_generate_article_data)
        resp = resp.json()
        print('associate urls with article objects')
        existing_urls = [i.url for i in articles]
        existing_mock_data = data.get('existing', {})
        existing_mock_data = {**existing_mock_data, **resp}
        for url, article in articles_url_association_dict.items():
            mock_url = existing_mock_data.get(url, None)
            if mock_url and mock_url not in existing_urls:
                article.url = mock_url
                try:
                    db.session.add(article)
                except Exception as e:
                    print(f'Exception at 219: {e}')
            else:
                try:
                    db.session.expunge(article)
                except Exception as e:
                    print(f'Exception at 224: {e}')
        print('done')
    except Exception as e:
        print(f'Exception at 227 {e}')
    db.session.commit()

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
            for i in current_user.read_articles if i.article is not None][:-6:-1]
    favs = [{'title': i.name, 'link': i.url} for i in current_user.fav_articles if i is not None][:-6:-1]
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
    read = [get_article_data(i.article) for i in current_user.read_articles if i.article is not None]
    favs = [get_article_data(i) for i in current_user.fav_articles if i is not None]
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

@app.route('/about/')
def about():
    return(render_template('index.html'))


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