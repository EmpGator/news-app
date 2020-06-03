import json
import math
from collections import Counter, defaultdict
from statistics import mean

from flask import Blueprint, render_template, url_for, redirect, request
from flask_login import current_user, login_required

from app import db
from app.models import Publisher, Analytics, User, PaymentHistory
from operator import attrgetter, itemgetter
from app.constants import Role

bp = Blueprint('publisher', __name__)


def dict_counter(attr, dictr):
    if attr in dictr:
        dictr[attr] += 1
    else:
        dictr[attr] = 1


@bp.route('/analytics')
@login_required
def analytics():
    """
    Fetches publisher relevant information to render on analytics page
    TODO: add new analytics data to object

    :return: Publisher analytics view
    """

    if current_user.role == Role.USER:
        return redirect(url_for('dashboard'))

    publisher = current_user.publisher
    revenue = get_percent_of_total_revenue(publisher)
    payment_percent = get_payment_percentages(publisher)
    articles = get_top_articles(publisher)
    anal = get_analytics_data()
    data = {'name': publisher.name, 'percent_of_total_revenue': revenue, 'payment_percent': payment_percent,
            'top_articles': articles, 'logo': publisher.image, **anal}

    data = json.dumps(data)
    return render_template('index.html', data=data)

@bp.route('/rssEdit', methods=['GET', 'POST'])
def edit_rss():
    if request.method == 'POST':
        url = request.form.get('rssUrl')
        if url:
            current_user.publisher.rss = url
            db.session.commit()
            return redirect(url_for('publisher.analytics'))
    return render_template('index.html')

@bp.route('/userdata')
@bp.route('/userdata/')
@login_required
def user_data():
    if current_user.role != Role.PUBLISHER:
        return redirect(url_for('dashboard'))
    users = User.query.filter(User.role == Role.USER)
    for user in users:
        if not hasattr(user, 'payment_history'):
            user.payment_history = [i.get_dict() for i in PaymentHistory.query.filter_by(user=user)]
            user.total_amount_spent = round(sum(p.get('value', 0) for p in user.payment_history), 2)
        else:
            print('user already has payment history')
        if not hasattr(user, 'amount_of_read_articles'):
            user.amount_of_read_articles = len([i for i in user.read_articles if i.article])
        else:
            print('user already has amount of articles')

    return render_template('user_table.html', users=users)

def get_analytics_data():
    devices = {}
    os = {}
    locations = {}
    traffics = defaultdict(int)
    durations = defaultdict(int)
    browsers = {}


    analytics = Analytics.query.all()
    total_dur = 0
    for a in analytics:
        dict_counter(a.device, devices)
        dict_counter(a.os, os)
        dict_counter(a.traffic.hour, traffics)
        dur = math.ceil(a.duration / 60)
        total_dur += dur
        dict_counter(dur, durations)
        dict_counter(a.browser, browsers)

    avg_dur = int(round(total_dur / len(analytics))) if analytics else 0
    max_dur = max(durations.keys()) if durations.keys() else 0
    min_dur = min(durations.keys()) if durations.keys() else 0
    min_traf = min(traffics, key=traffics.get) if traffics else 0
    max_traf = max(traffics, key=traffics.get) if traffics else 0

    devices = [{'name': i, 'amount': devices[i]} for i in devices]
    os = [{'name': i, 'amount': os[i]} for i in os]
    locations = []
    categories = []
    browsers = [{'name': i, 'amount': browsers[i]} for i in browsers]
    traffics = [{'time': i, 'amount': traffics[i]} for i in range(1, 25)]
    durations = [{'time': i, 'amount': durations[i]} for i in range(min_dur, max_dur + 1)]
    #durations = sorted([{'time': i, 'amount': durations[i]} for i in durations], key=itemgetter('time'))
    data = {'categories': categories, 'devices': devices, 'location': locations, 'browser': browsers,
            'os': os, 'duration_chart': durations, 'traffic_chart': traffics,
            'average_duration': avg_dur, 'min_duration': min_dur, 'max_duration': max_dur,
            'min_traffic': min_traf, 'max_traffic': max_traf}
    return data


def get_top_articles(publisher):
    """
    Fetches MAX_ARTICLES most popular articles of given publisher

    :param publisher: Publisher object

    :return: list of article objects

    """
    MIN_ARTICLES = 4
    MAX_ARTICLES = 15
    art = {'title': None, 'link': None, 'total_reads': 0, 'monthly_percent': 0, 'package_percent': 0, 'single_percent': 0}
    articles = [i.art_analytics_data() for i in sorted(publisher.articles, reverse=True,
                                                       key=attrgetter('hits'))[:MAX_ARTICLES] if i.hits]
    while len(articles) < MIN_ARTICLES:
        articles.append(art)
    return articles


def get_payment_percentages(publisher):
    """
    This calculates percentages of different payment types used to access given publisher articles

    :param publisher: Publisher object

    :return: dictionary with keys: monthly, package and single. Each contains rounded percentage

    """
    payment_percent = {'monthly': publisher.monthly_pay, 'package': publisher.package_pay,
                       'single': publisher.single_pay}
    all_together = sum(payment_percent.values()) or 1
    return {k: round(v / all_together, 1) for k, v in payment_percent.items()}


def get_percent_of_total_revenue(publisher):
    """
    This calculates total % of revenue this publisher has generated

    :param publisher: Publisher object

    :return: % of total revenue generated by given publisher, value between 0-1

    """

    from app import db
    from sqlalchemy.sql import func
    qry = db.session.query(func.sum(Publisher.revenue).label('total_revenue'))
    total = Publisher.query.filter_by(name='All').first()
    total_monthly_rev = total.revenue - total.single_pay - total.package_pay
    # total monthly revenue is needed to calculate how much revenue one monthly access has generated
    per_read_monthly_rev = total_monthly_rev / total.monthly_pay if total.monthly_pay else 0
    publisher_monthly_pay_rev = per_read_monthly_rev * publisher.monthly_pay
    pub_rev = publisher.single_pay + publisher.package_pay + publisher_monthly_pay_rev
    return round(pub_rev / total.revenue, 1) if total.revenue > 0 else 0
