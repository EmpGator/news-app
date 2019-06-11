from flask import Flask, session, render_template, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired


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
            return redirect(url_for('main'))
        else:
            return redirect(url_for('login'))

    return render_template('login.html', form=form)


@app.route('/')
def main():
    try:
        if session['user']:
            return render_template('index.html', id_list=list(range(5)))
    except Exception as e:
        print(e)
    return redirect(url_for('login'))


@app.route('/article/<id>')
def article(id=0):
    try:
        if session['user']:
            return f'allowed access for article {id}'
    except Exception as e:
        print(e)
    return f'access denied, log in'


if __name__ == '__main__':
    app.run(port=8000)
