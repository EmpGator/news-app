import os
import re
from datetime import date, timedelta
from pathlib import Path

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_jwt_extended import create_access_token
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message
from itsdangerous import URLSafeSerializer, BadSignature
from werkzeug.utils import secure_filename

from app.mail import mail
from app.constants import PUBLISHER_DOMAIN, BAD_CHAR_LIST, FINNPLUS_DOMAIN, PayOptions, MONTH_PRICE, SUBS_TIME, \
    BUNDLE_SIZE
from app.models import User, Publisher, PaymentHistory
from app.db import db
from passlib.hash import pbkdf2_sha256
from app.constants import Role


bp = Blueprint('auth', __name__)

def validate_email(email):
    if not re.match('[^@]+@[^@]+\.[^@]+', email):
        flash('Possibly bad email format')
        raise Exception('Possibly bad email format')
    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email address is taken')
        raise Exception('Email is taken')


def validate_name(name):
    if any(map(lambda i: i in name, BAD_CHAR_LIST)):
        flash('Bad character in name')
        raise Exception('bad character in name')


def validate_and_hash_password(pw, pw_again):
    if pw != pw_again:
        flash('passwords are different')
        raise Exception('different passwords')
    pw_hash = pbkdf2_sha256.hash(pw)
    return pw_hash


def send_confirm_email(user):
    # TODO: merge with password reset email
    sender = 'finnplus@gmx.com' #'tridample@gmail.com'
    msg = Message('Confirmation email',sender=sender, recipients=[user.email])
    serializer = URLSafeSerializer('verification_salt')
    token = serializer.dumps(user.id)
    msg.body = f'Finnplus account confirmation link: {FINNPLUS_DOMAIN}/activate/{token}'
    print(f'{FINNPLUS_DOMAIN}/activate/{token}')
    mail.send(msg)
    return 'Email sent'


def send_password_reset_mail(user):
    sender = 'finnplus@gmx.com' #'tridample@gmail.com'
    serializer = URLSafeSerializer('reset_salt')
    token = serializer.dumps(user.id)
    msg = Message('Password reset', sender=sender, recipients=[user.email])
    msg.body = f'Password reset link: {FINNPLUS_DOMAIN}/reset/{token}'
    print(f'{FINNPLUS_DOMAIN}/reset/{token}')
    mail.send(msg)
    return 'Email sent'


def pay_handler(option, user, amount=None):
    if option == PayOptions.MONTHLY:
        analytics = Publisher.query.filter_by(name='All').first()
        analytics.revenue += (MONTH_PRICE / 100)
        if user.subscription_end is None:
            user.subscription_end = date.today() + timedelta(days=SUBS_TIME)
        elif user.subscription_end <= date.today():
            user.subscription_end = date.today() + timedelta(days=SUBS_TIME)
        else:
            user.subscription_end += timedelta(days=SUBS_TIME)
        db.session.add(PaymentHistory(user=current_user, amount=29.99,  day=date.today(), pay_type='Monthly'))
    elif option == PayOptions.PACKAGE:
        user.prepaid_articles += BUNDLE_SIZE
        db.session.add(PaymentHistory(user=current_user, amount=5,  day=date.today(), pay_type='Package'))
    elif option == PayOptions.SINGLE:
        try:
            amount = int(amount)
        except Exception as e:
            print(e)
            amount = 0
        db.session.add(PaymentHistory(user=current_user, amount=amount/2,  day=date.today(), pay_type='Single'))
        user.tokens += amount
    else:
        return
    db.session.commit()

@bp.route('/signup', methods=['GET', 'POST'])
def new_entry():
    """
    Handles login form handling and show user login form

    TODO: split this to logical parts

    :return: View that is either same view with errors or new view
    """
    if request.method == 'POST':
        fn = request.form.get('firstName')
        ln = request.form.get('lastName')
        email = request.form.get('email')
        pw = request.form.get('password')
        pw_again = request.form.get('password')
        option = request.form.get('pay-method', "")
        option = PayOptions(option)
        amount = request.form.get('amount')

        try:
            validate_name(fn+ln)
            validate_email(email)
            pw_hash = validate_and_hash_password(pw, pw_again)
            # noinspection PyArgumentList
            new_user = User(first_name=fn, last_name=ln, email=email, password=pw_hash, role=Role.USER)
            db.session.add(new_user)
            db.session.commit()
            try:
                send_confirm_email(new_user)
            except Exception as e:
                print(e)
            login_user(new_user)
            access_token = create_access_token(identity=new_user.id)
            pay_handler(option, new_user, amount)
            publisher_domain_list = [i.url for i in Publisher.query.all()]
            return render_template('set_cookies.html', domains=publisher_domain_list, token=access_token,
                                   url_to=url_for('dashboard'))
        except Exception as e:
            print(e)
            return redirect(url_for('auth.new_entry'))

    return render_template('index.html')


@bp.route('/signin', methods=['GET', 'POST'])
def login():
    """
    handles login form and shows it to user

    :return: View that is either same view with errors or new view
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user is not None and pbkdf2_sha256.verify(request.form.get('password'), user.password):
            access_token = create_access_token(identity=user.id)
            print(access_token)

            login_user(user)
            publisher_domain_list = [i.url for i in Publisher.query.all()]
            return render_template('set_cookies.html', domains=publisher_domain_list, token=access_token,
                                   url_to=url_for('dashboard'))
        else:
            flash('Incorrect username or password ')

    return render_template('index.html')


@bp.route('/logout')
@login_required
def logout():
    """
    logout route, attempts to logout users from PUBLISHER_DOMAIN as well

    :return: Main page, not logged in
    """
    logout_user()
    publisher_domain_list = [i.url for i in Publisher.query.all()]
    return render_template('logout_all.html', domains=publisher_domain_list, url_to=url_for('index'))


@bp.route('/forgotpw', methods=['GET', 'POST'])
def forgotpw():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user and user.email_confirmed:
            try:
                send_password_reset_mail(user)
            except Exception as e:
                print(e)
            return redirect(url_for('index'))
        else:
            if not user:
                flash(f"User with email {email} doesn't exists")
            else:
                flash(f'You need to confirm email: {email} before you can reset password')

    return render_template('index.html')


@bp.route('/activate/<token>')
def activate(token=None):
    serializer = URLSafeSerializer('verification_salt')
    try:
        uid = serializer.loads(token)
        user = User.query.get(uid)
        user.email_confirmed = True
        db.session.commit()
        return redirect(url_for('dashboard'))
    except BadSignature:
        return 'Something went wrong'


@bp.route('/reset/<token>', methods=['POST', 'GET'])
def reset(token=None):
    serializer = URLSafeSerializer('reset_salt')
    try:
        uid = serializer.loads(token)
        user = User.query.get(uid)
    except BadSignature:
        return 'Something went wrong'
    if request.method == "POST":
        password = request.form.get('password')
        password2 = request.form.get('rPassword')
        if password == password2:
            user.password = pbkdf2_sha256.hash(password)
            db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('index.html')


@bp.route('/publisherRegister', methods=['GET', 'POST'])
def publisher_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        domain = request.form.get('domainName')
        email = request.form.get('email')
        rss = request.form.get('rssUrl')
        password = request.form.get('password')
        password_again = request.form.get('rPassword')
        img = request.files.get('photo-file')
        try:
            validate_name(name)
            validate_email(email)
            validate_and_hash_password(password, password_again)
        except Exception as e:
            return render_template('index.html')

        if img:
            ext = Path(img.filename).suffix
            file_name = name + ext
            path = os.path.join('app', 'static', 'media', secure_filename(file_name))
            img.save(path)
            img = url_for('static', filename=f'media/{file_name}')
        else:
            img = ''

        if password == password_again:
            password = pbkdf2_sha256.hash(password)
        pub = Publisher(name=name, url=domain, rss=rss, image=img)
        user = User(first_name=name, last_name='', email=email, password=password, role=Role.PUBLISHER, publisher=pub)
        db.session.add(pub)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('index.html')
