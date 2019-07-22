from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import Required


class PassResetForm(FlaskForm):
    password = PasswordField('new password', validators=[Required])