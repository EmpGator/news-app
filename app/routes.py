from flask import render_template, redirect, url_for, request, flash
from flask import current_app as app
from .models import db, User
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField
from wtforms.validators import DataRequired
from flask_login import current_user, login_user, logout_user, login_required


import pickle


class NewUserForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    payment_method = RadioField('Payment method', choices=[('1', 'Monthly'), ('0',
                                'Single')], default=1)


class LoginForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])


@app.route('/new', methods=['GET', 'POST'])
def new_entry():
    """Endpoint to create a user."""
    form = NewUserForm()
    if form.validate_on_submit():
        print('form validated')
        try:
            articles = []
            articles = pickle.dumps(articles)
            new_user = User(username=request.form.get('name'),
                            email=request.form.get('email'),
                            paid_articles=articles,
                            monthly_pay=bool(int(request.form.get('payment_method'))))
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            print(e)
            return render_template('new_user.html', form=form)
    else:
        print(form.errors.items())

    return render_template('new_user.html', form=form)


@app.route('/users')
@login_required
def users():
    """Lists all users"""
    users = User.query.all()
    return render_template('users.html', users=users, title="Show Users")


@app.route('/')
@login_required
def index():
    """Place holder for main page view """
    return render_template('index.html')

# placeholder
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print('user is authenticated')
        return redirect(url_for('index'))
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        print('user')
        if user is None:
            print('invalid username')
            return redirect(url_for('login'))
        print('user tries to log in')
        login_user(user)
        print('user logged in')
        return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """logoutroute"""
    logout_user()
    return redirect(url_for('login'))


@app.route('/article/<id>')
@login_required
def article(id=0):
    if current_user.monthly_pay:
        return render_template('article.html', article_id=id)
    else:
        paid_articles = pickle.loads(current_user.paid_articles)
        print(paid_articles)
        if request.url in paid_articles:
            return render_template('article.html', article_id=id)
        else:
            return render_template('blocked_article.html', article_id=id)
    return 'Something went wrong'


@app.context_processor
def utility_processor():
    def unpickle(pickled_string):
        return pickle.loads(pickled_string)
    return dict(unpickle=unpickle)
