from flask import render_template, redirect, url_for, request, make_response
from flask import current_app as app
from flask_jwt_extended import create_access_token

from .models import User, Publisher, Article
from flask_login import login_required, current_user
import feedparser
import json


def fetch_articles():
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
        obj = {'img': entry.media_content[0]['url'], 'title': entry.title, 'author': author, 'link': entry.link.replace('localhost', '127.0.0.1')}
        if i < 6:
            data['MrData'].append(obj)
        elif i < 12:
            data['TrData'].append(obj)
        else:
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


@app.route('/ts')
@login_required
def ts():
    return redirect('http://127.0.0.1:8000/ts/')


@app.route('/hs')
def hs():
    return redirect('http://127.0.0.1:8000/hs/')


@app.route('/kl')
def kl():
    return redirect('http://127.0.0.1:8000/kl/')


@app.route('/ks')
def ks():
    return redirect('http://127.0.0.1:8000/ks/')


@app.route('/ss')
def ss():
    return redirect('http://127.0.0.1:8000/ss/')


@app.route('/setcookie')
def setcookie():
    jwt = create_access_token(identity=current_user.id)
    resp = make_response(f'<img src="http://127.0.0.1:8000/setcookie/{jwt}" >', 200)
    return resp


@app.route('/test')
def test():
    from bs4 import BeautifulSoup
    import requests
    urls = []
    items = []
    title = None
    guid = None
    url = None
    image = None
    for b in ['hs', 'ks', 'kl', 'ts', 'ss']:
        for i in range(10):
            urls.append(f'http://localhost:8000/{b}/article/{i}')
    for url in urls:
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        images = soup.find_all('img')
        if len(images) > 2:
            image =  images[1].attrs.get('src')
            if image:
                guid = url[-1:]
                title = soup.find_all('h1')[0].text.strip()
                item = {'title': title, 'guid': guid, 'url': url, 'image': image}
                items.append(item)
    return render_template('test.xml', items=items)