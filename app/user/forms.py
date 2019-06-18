from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField


class Edit(FlaskForm):
    name = StringField('name')
    email = StringField('email')
    password = PasswordField('password')
