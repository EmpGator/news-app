import json

from flask import Blueprint, render_template, jsonify, url_for, redirect
from flask_login import current_user, login_required
from app.models import Publisher
from operator import attrgetter

bp = Blueprint('publisher', __name__)


# TODO Clean this up
@bp.route('/analytics')
@login_required
def analytics():
    try:
        if current_user.role != 'publisher':
            return redirect(url_for('dashboard'))

        publisher = current_user.publisher
        # get total revenues
        total = Publisher.query.filter_by(name='All').first()
        total_monthly_rev = total.revenue - total.single_pay - total.package_pay
        per_read_monthly_rev = total_monthly_rev / total.monthly_pay if total.monthly_pay else 0
        publisher_monthly_pay_rev = per_read_monthly_rev * publisher.monthly_pay

        # Payment type percentages
        payment_percent = {'monthly': publisher.monthly_pay, 'package': publisher.package_pay,
                           'single': publisher.single_pay}
        all_together = sum(payment_percent.values())
        if all_together == 0:
            all_together = 1
        payment_percent = {k: round(v / all_together, 1) for k, v in payment_percent.items()}

        # Most read articles

        articles = [{'name': i.name, 'hits': i.hits} for i in sorted(publisher.articles, reverse=True,
                                                                    key=attrgetter('hits'))[:4] if i.hits]
        # % of revenue this publisher generated
        pub_rev = publisher.single_pay + publisher.package_pay + publisher_monthly_pay_rev
        revenue = pub_rev / total.revenue if total.revenue > 0 else 0

        # Combine all data to one json
        data = {'name': publisher.name, 'revenue': revenue, 'payment_percent': payment_percent,
                'articles': articles}
        data = json.dumps(data)
    except Exception as e:
        print('error')
        print(e)
        data = []
    return render_template('index.html', data=data)
