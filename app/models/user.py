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
    
    first_name = db.Column(db.String(50), nullable=False)
    middle_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    password_salt = db.Column(db.String(32), nullable=False)
    
    role = db.Column(db.String(20), default='user')  # user, admin, superadmin

    date_joined = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_updated = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_seen = db.Column(db.DateTime(timezone=True), default=utcnow)
    email_verified = db.Column(db.Boolean, default=False)

    # Optional fields
    contact_no = db.Column(db.String(20), nullable=True)
    room_no = db.Column(db.String(20), nullable=True)

    building_id = db.Column(db.Integer, db.ForeignKey('building.id'), nullable=False)
    building = db.relationship("Building", back_populates="users")

    bookings = db.relationship("Booking", back_populates="user")

    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    course = db.relationship('Course', back_populates='users', lazy=True)

    def __repr__(self):
        """Representation of the User object."""
        return f"User(username={self.username}, email={self.email}, date_joined={self.date_joined})"
    
    @property
    def fullname(self):
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return ' '.join(parts)
    
    def is_admin(self):
        return self.role in ("admin", "superadmin")
    
    def is_superadmin(self):
        return self.role == "superadmin"
    
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
            'contact_no': self.contact_no,
            'room_no': self.room_no,
            'date_joined': User.format_datetime_to_str(self.date_joined),
            'last_updated': User.format_datetime_to_str(self.last_updated),
            'last_seen': User.format_datetime_to_str(self.last_seen),
            'email_verified': self.email_verified,
            'building': self.building.name,
            'course': self.course.name
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

    
    def get_reset_password_token(self, expires_sec=3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_password_token(token, expires_sec=3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, salt='password-reset-salt', max_age=expires_sec)
            user_id = data.get('user_id')
        except Exception:
            return None
        return User.query.get(user_id)