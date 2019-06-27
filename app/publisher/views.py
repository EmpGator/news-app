from flask import Blueprint, render_template, jsonify
from flask_login import current_user, login_required
from app.models import Publisher


bp = Blueprint('publisher', __name__)

# TODO Clean this up
@bp.route('/analytics')
@login_required
def analytics():
    try:
        data = []
        role = current_user.role
        total = Publisher.query.filter_by(name='All').first()
        total_monthly_rev = total.revenue - total.single_pay - total.package_pay


        if role == 'publisher':
            publisher = current_user.publisher
            monthly_rev_per = total_monthly_rev / (total.monthly_pay + 1 - publisher.monthly_pay)
            monthly = publisher.monthly_pay
            package = publisher.package_pay
            single = publisher.single_pay
            all = monthly + package + single
            monthly /= all
            package /= all
            single /= all
            articles = [ {'name': i.url, 'hits': i.hits}  for i in  publisher.articles if i.hits ]
            pub_rev = publisher.single_pay + publisher.package_pay + monthly_rev_per
            revenue = pub_rev / total.revenue
            payment_percent = {'monthly': monthly, 'package': package, 'single': single}
            data = {'name': publisher.name, 'revenue': revenue, 'payment_percent': payment_percent,
                    'articles': articles }
            return jsonify(data)
    except Exception as e:
        print('error')
        print(e)
        data = []
    return render_template('analytics/dashboard.html', data=data)
