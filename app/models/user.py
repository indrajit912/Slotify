# app/models/user.py
# 
# Author: Indrajit Ghosh
# Created On: May 10, 2025
# 
from datetime import datetime, date

# Third-party imports
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
import secrets
import uuid

# Local application imports
from app.extensions import db
from scripts.utils import utcnow, sha256_hash

class CurrentEnrolledStudent(db.Model):
    __tablename__ = 'enrolled_student'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    fullname = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    added_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f"<EnrolledStudent {self.fullname} ({self.email})>"

    def to_json(self):
        return {
            "uuid": self.uuid,
            "fullname": self.fullname,
            "email": self.email,
            "added_at": self.added_at.isoformat() if self.added_at else None
        }

    @classmethod
    def from_json(cls, data):
        return cls(
            uuid=data.get("uuid", uuid.uuid4().hex),
            fullname=data["fullname"],
            email=data["email"],
            added_at=datetime.fromisoformat(data["added_at"]) if data.get("added_at") else utcnow()
        )


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
    
    role = db.Column(db.String(20), default='user')  # user, admin, superadmin, guest

    date_joined = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_updated = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_seen = db.Column(db.DateTime(timezone=True), default=utcnow)
    email_verified = db.Column(db.Boolean, default=False)
    
    email_reminder_hours = db.Column(db.Integer, nullable=False, default=0)
    reminder_email = db.Column(db.String(120), nullable=True)  # Optional email ID for reminders

    # It will be for Guest only
    departure_date = db.Column(db.Date, nullable=True) 
    host_name = db.Column(db.String(255), nullable=True)

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
        return ' '.join(part for part in [self.first_name, self.middle_name, self.last_name] if part and part.strip())

    
    def is_admin(self):
        return self.role in ("admin", "superadmin")
    
    def is_superadmin(self):
        return self.role == "superadmin"
    
    def is_guest(self):
        return self.role == "guest"
    
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
    
    def is_email_reminder_on(self):
        """
        Returns True if the user has email reminders enabled.
        """
        return self.email_reminder_hours > 0

    def get_reminder_email(self):
        """
        Returns the email address to which reminders should be sent.
        Defaults to the user's primary email if reminder_email is not set.
        """
        return self.reminder_email or self.email
    
    def get_upcoming_bookings(self):
        """
        Returns a list of future bookings (today and later), sorted by date and time.
        """
        today = date.today()
        return sorted(
            [b for b in self.bookings if b.date >= today],
            key=lambda b: (b.date, b.time_slot.start_time)
        )

    def get_next_booking(self):
        """
        Returns the nearest upcoming booking (i.e., next in order).
        Returns None if no future bookings exist.
        """
        upcoming = self.get_upcoming_bookings()
        return upcoming[0] if upcoming else None

    def get_bookings_on(self, target_date):
        """
        Returns all bookings for the user on the given date.

        Args:
            target_date (datetime.date): Date to filter bookings.
        """
        return [
            b for b in self.bookings if b.date == target_date
        ]

    
    def to_json(self):
        """
        Convert the User instance into a JSON-serializable dictionary.
    
        Returns:
            dict: A dictionary representation of the user, including:
                - uuid (str): UUID of the user.
                - username (str)
                - first_name, middle_name, last_name (str | None)
                - email (str)
                - password_hash (str): Hashed password string.
                - password_salt (str): Salt used for hashing password.
                - role (str)
                - contact_no (str | None)
                - room_no (str | None)
                - date_joined (str): ISO datetime string.
                - last_updated (str)
                - last_seen (str)
                - email_verified (bool)
                - building_uuid (str | None): UUID of associated building.
                - course_uuid (str | None): UUID of associated course.
                - departure_date (str | None): ISO date string.
                - host_name (str | None)
        """
        return {
            "uuid": self.uuid,
            "username": self.username,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "email": self.email,
            "password_hash": self.password_hash,
            "password_salt": self.password_salt,
            "role": self.role,
            "contact_no": self.contact_no,
            "room_no": self.room_no,
            "date_joined": self.date_joined.isoformat() if self.date_joined else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "email_verified": self.email_verified,
            "building_uuid": self.building.uuid if self.building else None,
            "course_uuid": self.course.uuid if self.course else None,
            "departure_date": self.departure_date.isoformat() if self.departure_date else None,
            "host_name": self.host_name,
            "email_reminder_hours": self.email_reminder_hours,
            "reminder_email": self.reminder_email
        }
    
    @classmethod
    def from_json(cls, data, building_lookup, course_lookup):
        """
        Create a User instance from a JSON dictionary.
    
        Args:
            data (dict): JSON dictionary typically generated by `to_json()`.
            building_lookup (dict): Mapping of building UUIDs (str) to Building instances.
            course_lookup (dict): Mapping of course UUIDs (str) to Course instances.
    
        Returns:
            User: A new User instance with attributes populated from `data`.
                  The instance is not yet added to the database session.
    
        Raises:
            ValueError: If the building_uuid or course_uuid (if given) is not found in respective lookups.
    
        Usage:
            buildings = Building.query.all()
            building_lookup = {b.uuid: b for b in buildings}
            courses = Course.query.all()
            course_lookup = {c.uuid: c for c in courses}
    
            user = User.from_json(json_data, building_lookup, course_lookup)
        """
        def parse_dt(key):
            val = data.get(key)
            return datetime.fromisoformat(val) if val else None

        building = building_lookup.get(data.get("building_uuid"))
        if not building:
            raise ValueError(f"Building with UUID {data.get('building_uuid')} not found for User import")

        course = None
        if data.get("course_uuid"):
            course = course_lookup.get(data["course_uuid"])
            if not course:
                raise ValueError(f"Course with UUID {data['course_uuid']} not found for User import")

        return cls(
            uuid=data.get("uuid"),
            username=data.get("username"),
            first_name=data.get("first_name"),
            middle_name=data.get("middle_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
            password_hash=data.get("password_hash"),
            password_salt=data.get("password_salt"),
            role=data.get("role", "user"),
            contact_no=data.get("contact_no"),
            room_no=data.get("room_no"),
            date_joined=parse_dt("date_joined"),
            last_updated=parse_dt("last_updated"),
            last_seen=parse_dt("last_seen"),
            email_verified=data.get("email_verified", False),
            building=building,
            course=course,
            departure_date=parse_dt("departure_date"),
            host_name=data.get("host_name"),
            email_reminder_hours=data.get("email_reminder_hours", 0),
            reminder_email=data.get("reminder_email")
        )

    
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
    
    def generate_email_verification_token(self):
        """
        Generate a timed token for email verification.
        """
        serializer = URLSafeTimedSerializer(
            secret_key=current_app.config['SECRET_KEY'], salt='email-verification'
        )
        return serializer.dumps({'user_id': self.id})
    
    
    @staticmethod
    def verify_email_verification_token(token):
        """
        Verify the email verification token.
        """
        serializer = URLSafeTimedSerializer(
            secret_key=current_app.config['SECRET_KEY'], salt='email-verification'
        )
        try:
            data = serializer.loads(token, max_age=3600 * 24)
            user_id = data.get('user_id')
            if user_id:
                return User.query.get(user_id)
        except Exception:
            return None
    