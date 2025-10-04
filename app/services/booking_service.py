# app/services/booking_service.py
#
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
import logging
from datetime import date, timedelta, datetime

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
    Books a time slot for a given user (by UUID) on a specific date, enforcing:
    - max 3 bookings per machine per week
    - only one booking per user per day
    - no bookings on past dates
    - no bookings more than 3 months into the future

    Args:
        user_uuid (str): UUID of the user making the booking.
        slot_uuid (str): UUID of the time slot to be booked.
        day (date): The date for which the slot is to be booked.

    Returns:
        Booking: The newly created booking object.

    Raises:
        Exception: If the time slot is already booked, user exceeded limit, or date is invalid.
    """
    today = date.today()
    logger.info(f"Booking attempt: user_uuid={user_uuid}, slot_uuid={slot_uuid}, date={day}")

    if day < today:
        logger.warning(f"Rejected booking: date {day} is in the past.")
        raise Exception("You cannot book a slot on a past date.")

    if day > today + timedelta(days=90):
        logger.warning(f"Rejected booking: date {day} is more than 3 months ahead.")
        raise Exception("You cannot book more than 3 months in advance.")

    user = get_user_by_uuid(user_uuid)
    slot = get_time_slot_by_uuid(slot_uuid)

    if not user or not slot:
        logger.error(f"User or TimeSlot not found: user_uuid={user_uuid}, slot_uuid={slot_uuid}")
        raise ValueError("User or TimeSlot not found.")

    logger.info(f"User {user.id} and slot {slot.id} retrieved successfully.")

    monday = day - timedelta(days=day.weekday())  # start of the week
    sunday = monday + timedelta(days=6)           # end of the week

    weekly_count = (
        Booking.query
        .join(TimeSlot)
        .filter(
            Booking.user_id == user.id,
            Booking.date >= monday,
            Booking.date <= sunday,
            TimeSlot.machine_id == slot.machine_id
        )
        .count()
    )

    logger.debug(f"Weekly booking count for user {user.id} on machine {slot.machine_id}: {weekly_count}")
    if weekly_count >= 3:
        logger.warning(f"Booking limit exceeded: user {user.id} has {weekly_count} bookings this week.")
        raise Exception("Booking limit reached: You can book a maximum of 3 slots per machine per week.")

    existing_user_booking = (
        Booking.query
        .filter_by(user_id=user.id, date=day)
        .first()
    )
    if existing_user_booking:
        logger.warning(f"User {user.id} already has a booking on {day}.")
        raise Exception("You already have a booking on this date. Only one booking per day allowed.")

    existing = Booking.query.filter_by(time_slot_id=slot.id, date=day).first()
    if existing:
        logger.warning(f"Slot {slot.id} already booked on {day}.")
        raise Exception("Slot already booked")

    booking = Booking(user_id=user.id, time_slot_id=slot.id, date=day)
    db.session.add(booking)
    db.session.commit()

    logger.info(f"Booking successful: booking_id={booking.id}, user_id={user.id}, slot_id={slot.id}, date={day}")
    return booking

def cancel_booking_by_uuid(booking_uuid: str):
    """
    Cancel a booking by its UUID.

    Args:
        booking_uuid (str): UUID of the booking to cancel.

    Returns:
        dict: Information about the cancelled booking, including username and date.

    Raises:
        ValueError: If booking with given UUID does not exist.
        Exception: For other database errors.
    """
    booking = Booking.query.filter_by(uuid=booking_uuid).first()
    if not booking:
        raise ValueError(f"Booking with UUID {booking_uuid} not found.")

    # Capture details before deletion
    username = booking.user.username if booking.user else "Unknown"
    booking_date = booking.date

    try:
        db.session.delete(booking)
        db.session.commit()
        return {"username": username, "date": booking_date}
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Error cancelling booking: {e}")
    

def cancel_booking(user_uuid: str, slot_uuid: str, day: date):
    """
    Cancels an existing booking using user and slot UUIDs.

    Raises:
        Exception with descriptive message on errors.

    Returns:
        bool: True if booking was cancelled.
    """
    logger.info(f"Attempting to cancel booking: user_uuid={user_uuid}, slot_uuid={slot_uuid}, date={day}")

    user = get_user_by_uuid(user_uuid)
    if not user:
        msg = f"User not found for UUID: {user_uuid}"
        logger.error(msg)
        raise Exception(msg)

    slot = get_time_slot_by_uuid(slot_uuid)
    if not slot:
        msg = f"TimeSlot not found for UUID: {slot_uuid}"
        logger.error(msg)
        raise Exception(msg)

    now = datetime.now()

    if day < now.date():
        msg = f"Cannot cancel booking for past date: {day}"
        logger.warning(msg)
        raise Exception(msg)

    if day == now.date() and now.time() >= slot.start_hour:
        msg = f"Cannot cancel booking after slot start time ({slot.start_hour})"
        logger.warning(msg)
        raise Exception(msg)

    booking = Booking.query.filter_by(user_id=user.id, time_slot_id=slot.id, date=day).first()

    if not booking:
        msg = f"No booking found to cancel for user_uuid={user_uuid}, slot_uuid={slot_uuid}, date={day}"
        logger.warning(msg)
        raise Exception(msg)

    logger.info(f"Booking found (id={booking.id}), cancelling now.")
    db.session.delete(booking)
    db.session.commit()
    logger.info(f"Booking (id={booking.id}) cancelled successfully.")
    return True


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



