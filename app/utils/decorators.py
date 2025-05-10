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