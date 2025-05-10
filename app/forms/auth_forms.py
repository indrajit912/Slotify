# app/forms/auth_forms.py
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, IntegerField, HiddenField
from wtforms.validators import DataRequired, EqualTo, Optional, Length, Email, ValidationError


class UserLoginForm(FlaskForm):
    username_or_email = StringField("Username or Email address", validators=[DataRequired()])
    passwd = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class EmailRegistrationForm(FlaskForm):
    fullname = StringField("Fullname", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])

    submit = SubmitField("Next")