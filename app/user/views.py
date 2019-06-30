from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import date
from passlib.hash import pbkdf2_sha256
from app.db import db
from .forms import Edit

import json

bp = Blueprint('user', __name__)


@bp.route('/edit', methods=['POST', 'GET'])
@login_required
def edit():
    form = Edit()
    if form.validate_on_submit():
        try:
            if form.email.data:
                current_user.email = form.email.data
            if form.password.data:
                current_user.password = pbkdf2_sha256.hash(form.password.data)
            db.session.commit()
        except Exception as e:
            print(e)
            flash("Something went wrong, maybe email was already taken")
        return redirect(url_for('user.profile'))
    form.email.data = current_user.email
    return render_template('user/edit_user.html', form=form)


@bp.route('/profile')
@login_required
def profile():
    name = current_user.first_name + ' ' + current_user.last_name
    email = current_user.email
    bought = [i.url for i in current_user.articles]
    end = str(current_user.subscription_end) if current_user.subscription_end else None
    paid = current_user.prepaid_articles
    data = {'name': name, 'email': email, 'bought': bought, 'end_date': end,
            'prepaid': paid}
    data = json.dumps(data)
    return render_template('index.html', data=data)
