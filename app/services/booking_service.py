# app/services/booking_service.py
#
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
import logging
from datetime import date

from app.models.booking import Booking, TimeSlot
from app.extensions import db
from app.services.user_service import get_user_by_uuid

logger = logging.getLogger(__name__)

def get_time_slot_by_uuid(uuid_str: str):
    """
    Retrieves a TimeSlot from the database using its UUID.

    Args:
        uuid_str (str): UUID string of the TimeSlot.

    Returns:
        TimeSlot | None: The TimeSlot object if found, else None.
    """
    time_slot = TimeSlot.query.filter_by(uuid=uuid_str).first()
    if time_slot:
        logger.debug(f"TimeSlot found with UUID {uuid_str} (Slot #{time_slot.slot_number})")
    else:
        logger.warning(f"No TimeSlot found with UUID {uuid_str}")
    return time_slot


def book_slot(user_uuid: str, slot_uuid: str, day: date):
    """
    Books a time slot for a given user (by UUID) on a specific date.

    Args:
        user_uuid (str): UUID of the user making the booking.
        slot_uuid (str): UUID of the time slot to be booked.
        day (date): The date for which the slot is to be booked.

    Returns:
        Booking: The newly created booking object.

    Raises:
        Exception: If the time slot is already booked on the given date.
    """
    user = get_user_by_uuid(user_uuid)
    slot = get_time_slot_by_uuid(slot_uuid)

    if not user or not slot:
        raise ValueError("User or TimeSlot not found.")

    existing = Booking.query.filter_by(time_slot_id=slot.id, date=day).first()
    if existing:
        raise Exception("Slot already booked")

    booking = Booking(user_id=user.id, time_slot_id=slot.id, date=day)
    db.session.add(booking)
    db.session.commit()
    return booking

def cancel_booking(user_uuid: str, slot_uuid: str, day: date):
    """
    Cancels an existing booking using user and slot UUIDs.

    Args:
        user_uuid (str): UUID of the user.
        slot_uuid (str): UUID of the time slot.
        day (date): Date for which the booking is to be cancelled.

    Returns:
        bool: True if a booking was cancelled, False otherwise.
    """
    user = get_user_by_uuid(user_uuid)
    slot = get_time_slot_by_uuid(slot_uuid)

    if not user or not slot:
        return False

    booking = Booking.query.filter_by(user_id=user.id, time_slot_id=slot.id, date=day).first()
    if booking:
        db.session.delete(booking)
        db.session.commit()
        return True
    return False


def get_user_bookings(user_uuid: str):
    """
    Retrieves all bookings made by a specific user using UUID.

    Args:
        user_uuid (str): UUID of the user.

    Returns:
        list[Booking]: List of bookings made by the user, or an empty list if user not found.
    """
    user = get_user_by_uuid(user_uuid)
    if not user:
        logger.warning(f"get_user_bookings: No user found with UUID {user_uuid}")
        return []
    
    logger.debug(f"Retrieved {len(user.bookings)} bookings for user {user.username}")
    return user.bookings



