# app/services/user_service.py
#
# Author: Indrajit Ghosh
# Created On: May 11, 2025
# 
# User-related service functions for Slotify.
# Provides reusable functions for creating and retrieving user accounts.
#
import logging

from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.building import Building
from app.extensions import db
from scripts.utils import utcnow

logger = logging.getLogger(__name__)

def create_user(username, fullname, email, password, role="user", building_uuid=None):
    """
    Creates and stores a new user with hashed password and associated building.

    Args:
        username (str): Unique username.
        fullname (str): Full name of the user.
        email (str): User's email (must be unique).
        password (str): Plaintext password.
        role (str, optional): 'user', 'admin', or 'superadmin'. Defaults to 'user'.
        building_uuid (str, optional): UUID of the building where the user resides. Defaults to None.

    Returns:
        User: The created user object.

    Raises:
        ValueError: If email or username already exists, or if the building is not found.
    """
    if get_user_by_email(email):
        logger.warning(f"Email already registered: {email}")
        raise ValueError("Email already registered.")
    if get_user_by_username(username):
        logger.warning(f"Username already taken: {username}")
        raise ValueError("Username already taken.")

    logger.info(f"Creating new user: {username} ({email})")

    user = User(
        username=username,
        fullname=fullname,
        email=email,
        role=role
    )
    user.set_hashed_password(password=password)

    if building_uuid:
        building = Building.query.filter_by(uuid=building_uuid).first()
        if not building:
            logger.error(f"Building not found with UUID: {building_uuid}")
            raise ValueError(f"No building found with UUID: {building_uuid}")
        user.building = building

    db.session.add(user)
    try:
        db.session.commit()
        logger.info(f"User created successfully: {username} ({email})")
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Failed to create user {username} due to DB error: {e}")
        raise ValueError("Could not create user due to a database error.")

    return user


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
        **kwargs: Fields to update (e.g., fullname, email, password, role, username).

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

    if 'fullname' in kwargs:
        user.fullname = kwargs['fullname']

    if 'role' in kwargs:
        user.role = kwargs['role']

    if 'password' in kwargs:
        user.set_hashed_password(kwargs['password'])
        logger.debug(f"Password updated for user UUID {user_uuid}")

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
        logger.info(f"User's last_seen updated: {user_uuid}")
        return True

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating last_seen for user {user_uuid}: {e}")
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
