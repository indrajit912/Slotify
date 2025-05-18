"""
app/utils/token.py

Tokens for the Slotify application.

Author: Indrajit Ghosh
Created on: May 18, 2025
"""

import logging
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

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
