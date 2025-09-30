# Some utility functions
#
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#
import hashlib
import secrets
from datetime import datetime, timezone

def utcnow():
    """
    Get the current UTC datetime.

    Returns:
        datetime: A datetime object representing the current UTC time.
    """
    return datetime.now(timezone.utc)


def sha256_hash(raw_text:str):
    """Hash the given text using SHA-256 algorithm.

    Args:
        raw_text (str): The input text to be hashed.

    Returns:
        str: The hexadecimal representation of the hashed value.

    Example:
        >>> sha256_hash('my_secret_password')
        'e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4'
    """
    hashed = hashlib.sha256(raw_text.encode()).hexdigest()
    return hashed

def generate_token():
    # Generate a secure random token (hex string)
    token = secrets.token_hex(32)  # 64 chars long

    # Hash the token for storage (never store plain tokens in code)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    return token, token_hash