from flask_wtf import FlaskForm
from wtforms import RadioField, StringField
from wtforms.validators import DataRequired


class Edit(FlaskForm):
    name = StringField('name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    payment_method = RadioField('Payment method', choices=[(0, 'Single'), (1, 'Monthly')],
                                default=0, validators=[DataRequired()], coerce=int)
