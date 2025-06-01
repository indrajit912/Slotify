# app/utils/decorators.py
# Author: Indrajit Ghosh
# Created On: May 10, 2025

# Standard library imports
from functools import wraps

# Third-party imports
from flask import flash, redirect, url_for, request, jsonify
from flask_login import current_user, logout_user

from app.utils.token import verify_api_token

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

def email_verification_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        if not current_user.email_verified:
            logout_user()
            flash("Your email is not verified. Please verify your email before accessing this page.", "warning")
            return redirect(url_for("auth.login"))

        return func(*args, **kwargs)

    return decorated_function

def token_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
        else:
            return jsonify({'error': 'Missing or invalid token'}), 401

        user_uuid = verify_api_token(token)
        if not user_uuid:
            return jsonify({'error': 'Invalid or expired token'}), 403

        return f(user_uuid=user_uuid, *args, **kwargs)
    return decorated
