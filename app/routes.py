from flask import render_template, redirect, url_for, request
from flask import current_app as app
from .models import db, User
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class NewUserForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])


@app.route('/new', methods=['GET', 'POST'])
def new_entry():
    """Endpoint to create a user."""
    form = NewUserForm()
    if form.validate_on_submit():
        try:
            new_user = User(username=request.form.get('name'), email=request.form.get('email'))
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception as e:
            print(e)
            return render_template('new_user.html', form=form)
    return render_template('new_user.html', form=form)


@app.route('/users')
def users():
    """Lists all users"""
    users = User.query.all()
    return render_template('users.html', users=users, title="Show Users")


@app.route('/')
def index():
    return render_template('index.html')
