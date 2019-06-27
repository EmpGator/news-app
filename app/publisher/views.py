from flask import Blueprint, render_template
from flask_login import current_user, login_required
from app.models import Publisher


bp = Blueprint('publisher', __name__)


@bp.route('/analytics')
@login_required
def analytics():
    try:
        data = []
        role = current_user.role
        revenue = sum((i.revenue for i in Publisher.query.all()))

        if role == 'publisher':
            analytics = current_user.publisher
            combined_hits = sum((i.hits for i in analytics.articles))
            monthly = analytics.monthly_pay
            package = analytics.package_pay
            single = analytics.single_pay
            data.append(combined_hits)
            data.append(monthly)
            data.append(package)
            data.append(single)
            data.append(revenue)
    except AttributeError:
        data = []
    return render_template('analytics/dashboard.html', data=data)
