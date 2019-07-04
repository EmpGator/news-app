from flask import Flask, session, render_template, redirect, url_for, request, jsonify, make_response
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.secret_key = b'dsaadsads'

# TODO: logout logs user out from finnplus


class LoginForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


class Paywall:
    def __init__(self):
        self.show = False
        self.pay = False
        self.block = True

    def set_show(self):
        self.show = True
        self.pay = False
        self.block = False
        return self

    def set_pay(self):
        self.show = False
        self.pay = True
        self.block = False
        return self

    def set_block(self):
        self.show = False
        self.pay = False
        self.block = True
        return self


def show_content(url):
    auth = session.get('user', None)
    paywall = Paywall()
    payload = {'url': url}
    if not auth:
        print('not auth')
        jwt = session.get('accessToken', '')
        print(jwt)
        headers = {'Authorization': f'Bearer {jwt}'}
        r = requests.post('http://localhost:5000/api/userdata', data=payload, headers=headers)
    else:
        print('auth', auth)
        r = requests.post('http://localhost:5000/api/userdata', data=payload, auth=auth)
    if r.status_code == 200:
        data = r.json()
        if data['access']:
            return paywall.set_show()
        return paywall.set_pay()
    return paywall


@app.route('/loginfinnplus', methods=['POST'])
def loginfinnplus():
    """ handles login with finn plus account"""
    user = request.form.get('name')
    password = request.form.get('password')
    session['user'] = (user, password)
    return redirect(request.referrer)


@app.route('/logout')
def logout():
    """logout route"""
    session['user'] = None
    session['accessToken'] = None
    return render_template('logout_finnplus.html', url_to=url_for('index'))


@app.route('/')
def index():
    print(session.get('accessToken'))
    return render_template('index.html')


@app.route('/finnplus', methods=['POST'])
def finnplus():
    """ This informs finnplus that article has been paid """
    print('Posting to paidarticle')
    data = request.get_json()
    auth = session.get('user', None)

    if auth:
        r = requests.post('http://localhost:5000/api/articlepaid',
                          auth=auth, data=data)
    else:
        jwt = session.get('accessToken', '')
        headers = {'Authorization': f'Bearer {jwt}'}
        r = requests.post('http://localhost:5000/api/articlepaid',
                          headers=headers, data=data)
    print(r.status_code)
    print(r.text)
    if request.referrer is not None:
        return redirect(request.referrer)
    return redirect(url_for('index'))


@app.route('/<site>/')
def front(site='mock'):
    if site == 'favicon.ico':
        return redirect(url_for('static', filename='favicon.ico'))
    print(session.get('user'))
    return render_template(f'{site}/index.html')


@app.route('/<site>/article/<id>')
def news(site='mock', id=0):
    print('show content')
    show = show_content(str(request.url))
    form = LoginForm()
    return render_template(f'{site}/article_{id}.html', paywall=show, form=form)

@app.route('/setcookie/<jwt>')
def setcookie(jwt=None):
    url_to = request.args.get('url_to')
    print(jwt)
    session['accessToken'] = jwt
    return redirect(url_to)


if __name__ == '__main__':
    app.run(port=8000)
