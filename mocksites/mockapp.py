from flask import Flask, session, render_template, redirect, url_for, request, jsonify, make_response
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.secret_key = b'dsaadsads'


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
    if auth is None:
        return paywall.set_block()
    payload = {'url': url}
    r = requests.post('http://localhost:5000/api/userdata', data=payload, auth=auth)
    if r.status_code == 200:
        data = r.json()
        if data['access']:
            return paywall.set_show()
        return paywall.set_pay()



@app.route('/loginfinnplus', methods=['POST'])
def loginfinnplus():
    """ handles login with finnplus account"""
    user = request.form.get('name')
    password = request.form.get('password')
    session['user'] = (user, password)
    return redirect(request.referrer)


@app.route('/logout')
def logout():
    """logoutroute"""
    session['user'] = None
    return redirect(url_for('index'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/finnplus', methods=['POST'])
def finnplus():
    """ This informs finnplus that article has been paid """
    print('Posting to paidarticle')
    data = request.get_json()
    r = requests.post('http://localhost:5000/api/articlepaid',
                      auth=session['user'], data=data)
    print(r.status_code)
    print(r.text)
    if request.referrer is not None:
        return redirect(request.referrer)
    return redirect(url_for('index'))

# TODO: rename this
# TODO: 1st time routing to articles trough this, store token locally for afterwards
@app.route('/test', methods=['POST'])
def test():
    token = request.json.get('accessToken')
    new_url = request.json.get('url')
    session['user'] = (token, '')
    print(request.referrer)
    print(new_url)
    return redirect(request.referrer)

@app.route('/login')
def login():
    new_url = request.referrer
    return render_template('login.html', new_url=str(new_url))



@app.route('/<site>/')
def front(site='mock'):
    if site == 'favicon.ico':
        return redirect(url_for('static', filename='favicon.ico'))
    print(session.get('user'))
    return render_template(f'{site}/index.html')


@app.route('/<site>/article/<id>')
def news(site='mock', id=0):
    show = show_content(str(request.url))
    form = LoginForm()
    return render_template(f'{site}/article_{id}.html', paywall=show, form=form)

if __name__ == '__main__':
    app.run(port=8000)
