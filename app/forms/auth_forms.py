# app/forms/auth_forms.py
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, SelectField, DateField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, Email, Optional
from app.models.user import CurrentEnrolledStudent
from app.models.building import Building


class UserLoginForm(FlaskForm):
    username_or_email = StringField("Username or Email", validators=[DataRequired()])
    passwd = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log in")


class RegisterForm(FlaskForm):
    role_choice = SelectField(
        "Registering as", 
        choices=[("user", "ISI Resident"), ("guest", "Guest")],
        validators=[DataRequired()]
    )
    username = StringField("Username", validators=[DataRequired(), Length(max=100)])
    first_name = StringField("First Name", validators=[DataRequired(), Length(max=50)])
    middle_name = StringField("Middle Name", validators=[Length(max=50)])
    last_name = StringField("Last Name", validators=[Length(max=50)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password')])
    contact_no = StringField("Contact No", validators=[Length(max=20)])
    room_no = StringField("Room No", validators=[Length(max=20)])
    building_uuid = SelectField("Building", choices=[], validators=[DataRequired()])
    course_uuid = SelectField("Course", choices=[], validators=[Optional()])
    departure_date = DateField("Departure Date", validators=[Optional()])
    host_name = StringField(
        "Host Name", 
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "Whom you're visiting?"}
    )  
    submit = SubmitField("Register")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        if self.role_choice.data == "user":
            if not self.course_uuid.data:
                self.course_uuid.errors.append("Course is required for ISI Residents.")
                return False

            # ✅ Enrolled student email check
            email = self.email.data.lower()
            enrolled = CurrentEnrolledStudent.query.filter_by(email=email).first()
            if not enrolled:
                self.email.errors.append("This email is not listed in the ISI website. Please contact the admins.")
                return False
            
            # ✅ Check for RSH restriction
            if self.building_uuid.data:
                building = Building.query.filter_by(uuid=self.building_uuid.data).first()
                if building and building.code == "RSH" and not email.startswith("rs_"):
                    self.building_uuid.errors.append(
                        "You are not authorized to choose the RSH building. Please contact the admins."
                    )
                    return False

        if self.role_choice.data == "guest" and not self.departure_date.data:
            self.departure_date.errors.append("Departure date is required for Guests.")
            return False
        
        if self.role_choice.data == "guest" and not self.host_name.data.strip():
            self.host_name.errors.append("Host name is required for guests.")
            return False

        return True

    def validate_contact_no(self, field):
        if self.role_choice.data == 'guest' and not field.data:
            raise ValidationError("Contact number is required for guests.")


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Reset Password')