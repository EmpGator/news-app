from flask import Blueprint, render_template
from flask_login import current_user, login_required


bp = Blueprint('user', __name__)


@bp.route('/analytics')
@login_required
def analytics():
    try:
        data = current_user.data
    except AttributeError:
        data = []
    return render_template('analytics/dashboard.html', data=data)
