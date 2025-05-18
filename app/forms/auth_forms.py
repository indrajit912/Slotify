# app/forms/auth_forms.py
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, SelectField
from wtforms.validators import DataRequired, EqualTo, Optional, Length, Email


class UserLoginForm(FlaskForm):
    username_or_email = StringField("Username or Email address", validators=[DataRequired()])
    passwd = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class EmailRegistrationForm(FlaskForm):
    fullname = StringField("Fullname", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])

    submit = SubmitField("Next")

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=100)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    middle_name = StringField("Middle Name", validators=[Length(max=50)])
    last_name = StringField("Last Name", validators=[DataRequired(), Length(max=50)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    contact_no = StringField("Contact No", validators=[Length(max=20)])
    room_no = StringField("Room No", validators=[Length(max=20)])
    building_uuid = SelectField("Building", choices=[], validators=[DataRequired()])
    course_uuid = SelectField("Course", choices=[], validators=[DataRequired()])
    submit = SubmitField("Register")