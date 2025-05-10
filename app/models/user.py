# app/models/user.py
# 
# Author: Indrajit Ghosh
# Created On: May 10, 2025
# 

# Third-party imports
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
import secrets
import uuid

# Local application imports
from app.extensions import db
from scripts.utils import utcnow, sha256_hash

class User(db.Model, UserMixin):
    """
    User model for storing user related details.
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    username = db.Column(db.String(100), unique=True, nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    password_salt = db.Column(db.String(32), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, admin, superadmin

    date_joined = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_updated = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_seen = db.Column(db.DateTime(timezone=True), default=utcnow)
    email_verified = db.Column(db.Boolean, default=False)

    bookings = db.relationship("Booking", back_populates="user")

    def __repr__(self):
        """Representation of the User object."""
        return f"User(username={self.username}, email={self.email}, date_joined={self.date_joined})"
    
    def is_admin(self):
        return self.role in ("admin", "superadmin")
    
    def set_hashed_password(self, password):
        """
        Set hashed password for the user.

        Args:
            password (str): Plain text password to be hashed.
        """
        salt = secrets.token_hex(16)
        self.password_salt = salt

        password_with_salt = password + salt
        hashed_password = sha256_hash(password_with_salt)
        self.password_hash = hashed_password

    def check_password(self, password):
        """
        Check if the provided password matches the user's hashed password.

        Args:
            password (str): Plain text password to be checked.

        Returns:
            bool: True if password matches, False otherwise.
        """
        password_with_salt = password + self.password_salt
        hashed_password = sha256_hash(password_with_salt)
        return hashed_password == self.password_hash

    def avatar(self, size):
        """
        Generate Gravatar URL for the user's avatar.

        Args:
            size (int): Size of the avatar image.

        Returns:
            str: URL of the user's Gravatar avatar.
        """
        email_hash = sha256_hash(self.email.lower())
        return f"https://gravatar.com/avatar/{email_hash}?d=identicon&s={size}"
    
    
    def json(self):
        """
        Return dictionary representation of the user.

        Returns:
            dict: Dictionary containing user details.
        """
        return {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'fullname': self.fullname,
            'email': self.email,
            'role': self.role,
            'date_joined': User.format_datetime_to_str(self.date_joined),
            'last_updated': User.format_datetime_to_str(self.last_updated),
            'last_seen': User.format_datetime_to_str(self.last_seen),
            'email_verified': self.email_verified
        }
        
    
    @staticmethod
    def format_datetime_to_str(dt):
        """
        Formats a datetime object to the UTC string format: "Wed, 27 Mar 2024 07:10:10 UTC".

        Parameters:
            dt (datetime): A datetime object to be formatted.

        Returns:
            str: A string representing the datetime object in the UTC format.
        """
        return dt.strftime('%a, %d %b %Y %H:%M:%S UTC')

    
    def generate_email_verification_token(self):
        """
        Generate email verification token.

        Returns:
            str: Email verification token.
        """
        serializer = URLSafeTimedSerializer(
            secret_key=current_app.config['SECRET_KEY'], salt=b"email_verification"
        )
        return serializer.dumps({'user_id': self.id, 'email_verified': self.email_verified})
    
    @staticmethod
    def verify_email_verification_token(token):
        """
        Verify email verification token.

        Args:
            token (str): Email verification token.

        Returns:
            User or None: User object if token is valid, None otherwise.
        """
        serializer = URLSafeTimedSerializer(
            secret_key=current_app.config['SECRET_KEY'], salt=b"email_verification"
        )
        try:
            data = serializer.loads(token, max_age=3600 * 24)  # Token expires after 1 day
            user_id = data.get('user_id')
            email_verified = data.get('email_verified')
            if user_id is not None and email_verified is False:
                return User.query.get(user_id)
        except:
            pass
        return None