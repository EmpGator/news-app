from flask import Flask, session, render_template, redirect, url_for, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.secret_key = b'dsaadsads'
users = {'a': 'xyz', 'b': 'hjk'}


class LoginForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = form.name.data
        if users[user] == form.password.data:
            print('ok')
            session['user'] = user
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """logoutroute"""
    session['user'] = None
    return redirect(url_for('login'))


@app.route('/')
def index():
    return render_template('index.html', id_list=list(range(5)))


@app.route('/finnplus/')
def finnplus():
    auth = ('Test', 'asd')
    payload = {'url': str(request.referrer)}
    r = requests.post('http://localhost:5000/api/userdata', data=payload, auth=auth)
    data = r.json()
    show_content = data['user']['Monthly payment']
    if show_content:
        session['user'] = data['user']
        return redirect(request.referrer)
    return redirect(url_for('index'))


@app.route('/article/<id>')
def article(id=0):
    try:
        if session['user']:
            return render_template('article.html', article_id=id)
    except Exception as e:
        print(e)
    return render_template('blocked_article.html', article_id=id)


@app.route('/api')
def api():
    return jsonify(users)


if __name__ == '__main__':
    app.run(port=8000)
