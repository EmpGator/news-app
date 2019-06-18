from flask import Blueprint, render_template, request
from flask_login import current_user, login_required
from .forms import Edit
from datetime import date
bp = Blueprint('user', __name__)


@bp.route('/edit', methods=['POST', 'GET'])
@login_required
def edit():
    form = Edit()
    print(current_user)
    form.name.data = current_user.username
    form.email.data = current_user.email
    form.payment_method.data = int(current_user.monthly_pay)
    return render_template('user/edit_user.html', form=form)


@bp.route('/pay')
@login_required
def pay():
    payment_button = False
    print(current_user.subscription_end)
    print(type(current_user.subscription_end))
    if current_user.monthly_pay:
        if current_user.subscription_end is None:
            payment_button = True
        elif current_user.subscription_end <= date.today():
            payment_button = True

    return render_template('user/pay_month.html', button=payment_button)
