from datetime import datetime, date
from flask import render_template, redirect, url_for, request, make_response
from flask import current_app as app
from flask_jwt_extended import create_access_token
from flask_login import login_required, current_user
from app.constants import PUBLISHER_DOMAIN, Role, Category
from app.models import Article, Publisher
from app.db import db
import feedparser
import json


def get_articles(publishers=None, categories=None):
    """
    Fetches articles from database and adds them obj that is rendered then in frontpage

    :return: article data in python dictionary

    """
    data = {'MrData': [], 'TrData': [], 'LtData': []}
    if publishers and categories:
        articles = Article.query.filter(Article.publisher.in_(publishers),
                                        Article.category.in_(categories))
    elif publishers:
        articles = Article.query.filter(Article.publisher.in_(publishers))
    elif categories:
        articles = Article.query.filter(Article.category.in_(categories))
    else:
        articles = Article.query.filter(Article.image.isnot(None))

    for i, entry in enumerate(articles):
        art_data = get_article_data(entry)
        if i < 6:
            data['MrData'].append(art_data)
        elif i < 12:
            data['TrData'].append(art_data)
        elif i < 18:
            data['LtData'].append(art_data)
        else:
            break
    return data

def get_articles2(publishers=None, categories=None):
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
        data.append(dict(name=headline, content=art_data_lst))
    print(json.dumps(data))

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


@app.route('/fetch_articles')
def fetch_articles():
    """
    Fetches articles from rss feed
    TODO: make this background task to be executed one in a while


    :return: Response: OK, 200
    """
    url_list = [f'http://{PUBLISHER_DOMAIN}/{i}/rss' for i in ['ts', 'hs', 'ks', 'kl', 'ss']]
    for src in url_list:
        feed = feedparser.parse(src)
        try:
            url = feed.feed.link.replace('http://', '')
        except:
            return make_response(f'{feed}\n{src}')
        author = Publisher.query.filter_by(url=url).first()
        if author:
            for i, entry in enumerate(feed.entries):
                url = entry.link
                if not Article.query.filter_by(url=url).first():
                    img = entry.media_content[0]['url']
                    if not img:
                        img = author.image
                    category = Category(entry.category)
                    day = date.fromisoformat(entry.published)
                    article = Article(name=entry.title, publisher=author, image=img, url=url,
                                      description=entry.description, date=day, category=category)
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
    get_articles2()
    if current_user.role == Role.PUBLISHER:
        return redirect(url_for('publisher.analytics'))

    art_data = get_articles()
    # Temp start
    name = current_user.first_name + ' ' + current_user.last_name
    email = current_user.email
    bought = current_user.prepaid_articles
    end = str(current_user.subscription_end) if current_user.subscription_end else None
    paid = current_user.prepaid_articles
    read = [{'title': i.article.name, 'link': i.article.url, 'accessed': str(i.day)} for i in current_user.read_articles][:-6:-1]
    user_data = {'name': name, 'email': email, 'bought': bought, 'end_date': end,
            'prepaid': paid, 'tokens': current_user.tokens, 'latestArticles': read}
    # Temp end
    data = {**art_data, **user_data}
    data = json.dumps(data)
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
