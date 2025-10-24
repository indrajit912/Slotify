"""
app/utils/token.py

Tokens for the Slotify application.

Author: Indrajit Ghosh
Created on: May 18, 2025
"""
import logging
import hmac

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired, URLSafeSerializer
from flask import current_app
from app.services import get_user_by_uuid
from config import Config

from scripts.utils import utcnow, sha256_hash

logger = logging.getLogger(__name__)


def generate_registration_token(data):
    """
    Generate a time-stamped registration token for email confirmation.

    Args:
        data (dict or str): Data to encode in the token (e.g., user email or UUID).

    Returns:
        str: Signed token string.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(data, salt='register')
    logger.debug("Generated registration token.")
    return token


def confirm_registration_token(token, expiration=86400): # 24 Hrs
    """
    Confirm and decode a registration token within a time window.

    Args:
        token (str): The signed token string to decode.
        expiration (int): Time in seconds before the token expires. Defaults to 24 hours.

    Returns:
        str or dict or None: Decoded data if valid; None if invalid or expired.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(token, salt='register', max_age=expiration)
        logger.debug("Registration token successfully verified.")
        return data
    except SignatureExpired:
        logger.warning("Registration token expired.")
        return None
    except BadSignature:
        logger.warning("Invalid registration token signature.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None

def generate_api_token(user_uuid, expires_in_days=1):
    user = get_user_by_uuid(uuid_str=user_uuid)
    if not user:
        raise ValueError("User not found")
    
    s = URLSafeSerializer(current_app.config['SECRET_KEY'])
    payload = {
        'user_uuid': str(user.uuid),
        'iat': utcnow().timestamp(),
        'exp': utcnow().timestamp() + expires_in_days * 86400
    }
    return s.dumps(payload, salt='api-auth')

def verify_api_token(token):
    s = URLSafeSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='api-auth')
        exp = data.get('exp')
        if exp and utcnow().timestamp() > exp:
            return None
        # Get the user_uuid from the data
        user_uuid = data.get('user_uuid')

        # Get the user
        user = get_user_by_uuid(uuid_str=user_uuid)
        data['is_admin'] = user.is_admin()
        data['is_superadmin'] = user.is_superadmin()
        data['is_guest'] = user.is_guest()
        data['role'] = user.role
        return data
    except Exception:
        return None


def verify_import_token(token: str) -> bool:
    if not Config.IMPORT_TOKEN_HASH:
        return False
    token_hash = sha256_hash(token)
    return hmac.compare_digest(token_hash, Config.IMPORT_TOKEN_HASH)

def generate_admin_verification_code(admin_email: str, user_email: str) -> str:
    """
    Generate a signed Admin Verification Code (AVC).
    This code can be used by any users to verify their email id with admin approval.
    It will bypass the usual email verification process if the user provides a valid AVC.
    This is typically used when an admin manually approves a user registration.
    This is a confirmation that the admin has verified the user's email.
    """
    serializer = URLSafeSerializer(current_app.config["SECRET_KEY"], salt="admin-verification-code")
    payload = {
        "admin_email": admin_email,
        "user_email": user_email,
        "issued_at": utcnow().isoformat()
    }
    return serializer.dumps(payload)

def verify_admin_verification_code(code: str):
    """Return decoded data if valid, otherwise None."""
    serializer = URLSafeSerializer(current_app.config["SECRET_KEY"], salt="admin-verification-code")
    try:
        data = serializer.loads(code)
        return data  # contains 'admin_email', 'user_email', 'issued_at'
    except BadSignature:
        return None
    

