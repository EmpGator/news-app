from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, PasswordField
from wtforms.validators import DataRequired


class NewUserForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    payment_method = RadioField('Payment method', choices=[('1', 'Monthly'),
                                ('0', 'Single')], default=1,
                                validators=[DataRequired()])


class LoginForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])