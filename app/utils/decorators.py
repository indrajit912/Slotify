# app/utils/decorators.py
# Author: Indrajit Ghosh
# Created On: May 10, 2025

# Standard library imports
from functools import wraps

# Third-party imports
from flask import flash, redirect, url_for
from flask_login import current_user

def logout_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            flash("You are already registered.", "info")
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)

    return decorated_function

def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Access restricted. Your account lacks the necessary permissions.", "info")
            return redirect(url_for("auth.dashboard"))
        return func(*args, **kwargs)

    return decorated_function