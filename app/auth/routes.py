# app/auth/routes.py
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#
# Standard library imports
import logging

# Third-party imports
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

# Relative imports
from . import auth_bp
from app.forms.auth_forms import UserLoginForm
from app.utils.decorators import logout_required

logger = logging.getLogger(__name__)

# Login view (route)
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLoginForm()

    # Login logic here
    if form.validate_on_submit():

        # TODO: Check if the user provided username or email
                
        form = UserLoginForm(formdata=None)

    return render_template('login.html', form=form)


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully!", 'success')
    logger.info("User logged out successfully.")

    return redirect(url_for('auth.login'))


@auth_bp.route('/register_email', methods=['GET', 'POST'])
@logout_required
def register_email():
    return "This is register_email"

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return "This is forgot_password."