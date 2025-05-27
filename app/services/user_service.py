# app/services/user_service.py
#
# Author: Indrajit Ghosh
# Created On: May 11, 2025
# 
# User-related service functions for Slotify.
# Provides reusable functions for creating and retrieving user accounts.
#
import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.course import Course
from app.models.building import Building
from app.extensions import db
from scripts.utils import utcnow

logger = logging.getLogger(__name__)

# TODO: Create methods for CurrentEnrolledStudents

def create_user(
    *,
    username: str,
    first_name: str,
    email: str,
    password: str,
    building_uuid: str,
    role: str | None = None,
    contact_no: str | None = None,
    room_no: str | None = None,
    course_uuid: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    email_verified: bool = False,
    departure_date = None,
    host_name = None
):
    if get_user_by_email(email):
        logger.warning(f"Email already registered: {email}")
        raise ValueError("Email already registered.")
    if get_user_by_username(username):
        logger.warning(f"Username already taken: {username}")
        raise ValueError("Username already taken.")

    if not username:
        raise ValueError("Username is required.")
    if not first_name:
        raise ValueError("First name is required.")
    if not email:
        raise ValueError("Email is required.")
    if not password:
        raise ValueError("Password is required.")
    if not building_uuid:
        raise ValueError("Building UUID is required.")

    logger.info(f"Creating new user: {username} ({email})")

    # Fetch building and course first
    building = Building.query.filter_by(uuid=building_uuid).first()
    if not building:
        logger.error(f"Building not found with UUID: {building_uuid}")
        raise ValueError(f"No building found with UUID: {building_uuid}")

    course = None
    if course_uuid:
        course = Course.query.filter_by(uuid=course_uuid).first()
        if not course:
            logger.error(f"Course not found with UUID: {course_uuid}")
            raise ValueError(f"No course found with UUID: {course_uuid}")

    # Create user with relationships assigned
    user = User(
        username=username,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        email=email,
        contact_no=contact_no,
        room_no=room_no,
        role=role,
        email_verified=email_verified,
        building=building,
        course=course,
        departure_date=departure_date,
        host_name = host_name
    )
    user.set_hashed_password(password=password)

    db.session.add(user)  # ✅ Add to session before setting relationships

    try:
        db.session.commit()
        logger.info(f"User created successfully: {username} ({email})")
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Failed to create user {username} due to DB error: {e}")
        raise ValueError("Could not create user due to a database error.")

    return user

def get_all_admins():
    """
    Returns a list of all users with role 'admin' or 'superadmin'.
    """
    return User.query.filter(User.role.in_(['admin', 'superadmin'])).all()


def get_user_by_uuid(uuid_str: str):
    """
    Retrieves a user from the database by their UUID.

    Args:
        uuid_str (str): UUID string of the user.

    Returns:
        User | None: The User object if found, else None.
    """
    user = User.query.filter_by(uuid=uuid_str).first()
    if user:
        logger.debug(f"User found with UUID {uuid_str}: {user.username}")
    else:
        logger.warning(f"No user found with UUID {uuid_str}")
    return user

def get_user_by_email(email):
    """
    Fetch a user by email.

    Args:
        email (str): Email address to look up.

    Returns:
        User or None
    """
    user = User.query.filter_by(email=email).first()
    if user:
        logger.debug(f"User found by email: {email}")
    else:
        logger.debug(f"No user found with email: {email}")
    return user


def get_user_by_username(username):
    """
    Fetch a user by username.

    Args:
        username (str): Username to look up.

    Returns:
        User or None
    """
    user = User.query.filter_by(username=username).first()
    if user:
        logger.debug(f"User found by username: {username}")
    else:
        logger.debug(f"No user found with username: {username}")
    return user


def update_user_by_uuid(user_uuid, **kwargs):
    """
    Updates fields of an existing user using UUID.

    Args:
        user_uuid (str): The UUID of the user to update.
        **kwargs: Fields to update (e.g., first_name, middle_name, last_name, email, password, role,
                  username, course_uuid, building_uuid, contact_no, room_no, email_verified).

    Returns:
        User: The updated user object.

    Raises:
        ValueError: If the user does not exist or if email/username already in use.
    """
    user = User.query.filter_by(uuid=user_uuid).first()
    if not user:
        logger.warning(f"Attempted to update non-existent user UUID: {user_uuid}")
        raise ValueError("User not found.")

    logger.info(f"Updating user {user.username} (UUID: {user_uuid})")

    if 'username' in kwargs:
        new_username = kwargs['username']
        if new_username != user.username and get_user_by_username(new_username):
            logger.warning(f"Username already taken: {new_username}")
            raise ValueError("Username already taken.")
        user.username = new_username

    if 'email' in kwargs:
        new_email = kwargs['email']
        if new_email != user.email and get_user_by_email(new_email):
            logger.warning(f"Email already registered: {new_email}")
            raise ValueError("Email already registered.")
        user.email = new_email
        user.email_verified = False
    
    if 'email_verified' in kwargs:
        new_val = kwargs['email_verified']
        user.email_verified = new_val
        logger.info(f"{user.username}'s email_verified updated to '{new_val}'.")

    # Update name parts individually or via fullname if provided
    if 'fullname' in kwargs:
        name_parts = kwargs['fullname'].strip().split()
        if len(name_parts) == 0:
            raise ValueError("Full name must contain at least one word.")
        user.first_name = name_parts[0]
        user.middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else None
        user.last_name = name_parts[-1] if len(name_parts) > 1 else ""
    else:
        # If individual name parts are given
        if 'first_name' in kwargs:
            user.first_name = kwargs['first_name']
        if 'middle_name' in kwargs:
            user.middle_name = kwargs['middle_name']
        if 'last_name' in kwargs:
            user.last_name = kwargs['last_name']

    if 'role' in kwargs:
        user.role = kwargs['role']

    if 'password' in kwargs:
        user.set_hashed_password(kwargs['password'])
        logger.debug(f"Password updated for user UUID {user_uuid}")

    if 'contact_no' in kwargs:
        user.contact_no = kwargs['contact_no']

    if 'room_no' in kwargs:
        user.room_no = kwargs['room_no']

    if 'building_uuid' in kwargs:
        building_uuid = kwargs['building_uuid']
        if building_uuid:
            building = Building.query.filter_by(uuid=building_uuid).first()
            if not building:
                logger.error(f"Building not found with UUID: {building_uuid}")
                raise ValueError(f"No building found with UUID: {building_uuid}")
            user.building = building
        else:
            user.building = None  # Allow clearing building

    if 'course_uuid' in kwargs:
        course_uuid = kwargs['course_uuid']
        if course_uuid:
            course = Course.query.filter_by(uuid=course_uuid).first()
            if not course:
                logger.error(f"Course not found with UUID: {course_uuid}")
                raise ValueError(f"No course found with UUID: {course_uuid}")
            user.course = course
        else:
            user.course = None  # Allow clearing course

    if 'departure_date' in kwargs:
        try:
            if kwargs['departure_date']:
                if isinstance(kwargs['departure_date'], str):
                    user.departure_date = datetime.strptime(kwargs['departure_date'], "%Y-%m-%d").date()
                else:
                    user.departure_date = kwargs['departure_date']
            else:
                user.departure_date = None  # allow clearing the date
        except Exception as e:
            logger.error(f"Invalid departure_date: {kwargs['departure_date']} — {e}")
            raise ValueError("Invalid departure_date format. Use 'YYYY-MM-DD'.")


    if kwargs:
        user.last_updated = utcnow()

    try:
        db.session.commit()
        logger.info(f"User {user.username} (UUID: {user_uuid}) updated successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user UUID {user_uuid}: {e}")
        raise ValueError("Could not update user.")

    return user


def update_user_last_seen(user_uuid: str):
    """
    Updates the 'last_seen' field of a user with the current timestamp.

    Args:
        user_uuid (str): UUID of the user whose last_seen field will be updated.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    try:
        # Retrieve the user by UUID
        user = get_user_by_uuid(user_uuid)
        if not user:
            logger.warning(f"User not found: {user_uuid}")
            return False
        
        # Update the 'last_seen' field to the current timestamp
        user.last_seen = utcnow()
        
        # Commit the changes to the database
        db.session.commit()
        logger.info(f"User's last_seen updated: {user.username}")
        return True

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating last_seen for user {user.username} <{user.uuid}>: {e}")
        return False

def delete_user_by_uuid(user_uuid):
    """
    Deletes a user by UUID.

    Args:
        user_uuid (str): The UUID of the user to delete.

    Returns:
        bool: True if deleted successfully.

    Raises:
        ValueError: If the user does not exist.
    """
    user = User.query.filter_by(uuid=user_uuid).first()
    if not user:
        logger.warning(f"Attempted to delete non-existent user UUID: {user_uuid}")
        raise ValueError("User not found.")

    logger.info(f"Deleting user {user.username} (UUID: {user_uuid})")

    db.session.delete(user)
    try:
        db.session.commit()
        logger.info(f"User {user.username} (UUID: {user_uuid}) deleted successfully.")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user UUID {user_uuid}: {e}")
        raise ValueError("Could not delete user.")
