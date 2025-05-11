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
from app.models.user import User
from app.services import update_user_last_seen
from app.utils.decorators import logout_required

logger = logging.getLogger(__name__)

@auth_bp.before_request
def update_last_seen():
    if current_user.is_authenticated:
        user_uuid = current_user.uuid
        status = update_user_last_seen(user_uuid)

        if not status:
            logger.error(f"Updating last seen failed for '{current_user.username}'")

# Login view (route)
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLoginForm()

    if form.validate_on_submit():
        user_input = form.username_or_email.data
        user = User.query.filter(
            (User.username == user_input) | (User.email == user_input)
        ).first()

        if user:
            if user.check_password(form.passwd.data):
                login_user(user)
                logger.info(f"User '{user.email}' successfully logged in.")
                flash("Login successful!", 'success')
                return redirect(url_for('auth.dashboard'))
            else:
                flash("Wrong password. Try again!", 'error')
                logger.warning(f"Failed login attempt: incorrect password for '{user_input}'")
        else:
            flash("That user doesn't exist! Try again...", 'error')
            logger.warning(f"Failed login attempt: no such user '{user_input}'")

        form = UserLoginForm(formdata=None)

    return render_template('login.html', form=form)


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard view for logged-in users.

    Returns:
        Rendered HTML template for the dashboard.
    """
    return render_template('dashboard.html', user=current_user)


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