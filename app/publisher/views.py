import json

from flask import Blueprint, render_template, jsonify, url_for, redirect
from flask_login import current_user, login_required
from app.models import Publisher

bp = Blueprint('publisher', __name__)


# TODO Clean this up
# TODO redirect users of wrong role to dashboard
@bp.route('/analytics')
@login_required
def analytics():
    try:
        data = []
        role = current_user.role
        if role != 'publisher':
            return redirect(url_for('dashboard'))
        total = Publisher.query.filter_by(name='All').first()
        total_monthly_rev = total.revenue - total.single_pay - total.package_pay

        if role == 'publisher':
            publisher = current_user.publisher
            divider = (total.monthly_pay - publisher.monthly_pay)
            if divider == 0:
                divider = 1
            monthly_rev_per = total_monthly_rev / divider
            monthly = publisher.monthly_pay
            package = publisher.package_pay
            single = publisher.single_pay
            all_together = monthly + package + single
            if all_together == 0:
                all_together = 1
            monthly /= all_together
            package /= all_together
            single /= all_together
            monthly = round(monthly, 1)
            package = round(package, 1)
            single = round(single, 1)
            articles = [{'name': i.url, 'hits': i.hits} for i in publisher.articles if i.hits]
            pub_rev = publisher.single_pay + publisher.package_pay + monthly_rev_per
            revenue = pub_rev / total.revenue if total.revenue > 0 else 0
            payment_percent = {'monthly': monthly, 'package': package, 'single': single}
            data = {'name': publisher.name, 'revenue': revenue, 'payment_percent': payment_percent,
                    'articles': articles}
            data = json.dumps(data)
    except Exception as e:
        print('error')
        print(e)
        data = []
    return render_template('index.html', data=data)
