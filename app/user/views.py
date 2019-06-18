from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required
from datetime import date
from passlib.hash import pbkdf2_sha256
from app.db import db
from .forms import Edit

bp = Blueprint('user', __name__)


@bp.route('/edit', methods=['POST', 'GET'])
@login_required
def edit():
    form = Edit()
    if form.validate_on_submit():
        if form.name.data:
            current_user.username = form.name.data
        if form.email.data:
            current_user.email = form.email.data
        if form.password.data:
            current_user.password = pbkdf2_sha256.hash(form.password.data)
        db.session.commit()
        return redirect(url_for('index'))

    form.name.data = current_user.username
    form.email.data = current_user.email
    return render_template('user/edit_user.html', form=form)


@bp.route('/pay')
@login_required
def pay():
    payment_button = False
    subs = False
    if current_user.subscription_end is None:
        payment_button = True
    elif current_user.subscription_end <= date.today():
        payment_button = True

    if current_user.subscription_end is not None:
        subs = True

    return render_template('user/pay_month.html', button=payment_button, subs=subs)
