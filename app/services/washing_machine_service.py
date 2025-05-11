# app/services/washing_machine_service.py
#
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
import logging
import calendar
from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import extract

from app.models.washingmachine import WashingMachine
from app.models.booking import TimeSlot, Booking
from app.extensions import db

logger = logging.getLogger(__name__)

# TODO: Write a function that can check whether a list of time_range is valid (i.e. not coinciding)

def create_washing_machine(name: str, time_slots: list[dict]):
    """
    Creates a new washing machine with given time slots.

    Args:
        name (str): Name of the washing machine.
        time_slots (list of dict): Each dict should have 'slot_number' and 'time_range'.
            Example: [
                        {"slot_number": 1, "time_range": "07:00-10:30"},
                        {"slot_number": 2, "time_range": "11:30-15:00"},
                        ...
                     ]

    Returns:
        WashingMachine: The created machine object.

    Raises:
        ValueError: If the machine name already exists.
    """
    if WashingMachine.query.filter_by(name=name).first():
        logger.warning(f"WashingMachine name already exists: {name}")
        raise ValueError("Washing machine name already exists.")

    machine = WashingMachine(name=name)
    db.session.add(machine)
    db.session.flush()  # So we get machine.id before committing

    for slot in time_slots:
        ts = TimeSlot(
            machine_id=machine.id,
            slot_number=slot["slot_number"],
            time_range=slot["time_range"]
        )
        db.session.add(ts)

    try:
        db.session.commit()
        logger.info(f"WashingMachine '{name}' created with {len(time_slots)} slots.")
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Failed to create machine {name}: {e}")
        raise ValueError("Could not create machine due to a database error.")

    return machine


def get_all_machines():
    return WashingMachine.query.all()

def delete_washing_machine_by_uuid(uuid_str: str):
    """
    Deletes a washing machine (and its time slots and related bookings) by its UUID.

    Args:
        uuid_str (str): The UUID of the washing machine to delete.

    Returns:
        bool: True if deletion was successful, False otherwise.

    Raises:
        ValueError: If no machine is found with the given UUID.
    """
    machine = WashingMachine.query.filter_by(uuid=uuid_str).first()
    if not machine:
        logger.warning(f"No washing machine found with UUID: {uuid_str}")
        raise ValueError("Washing machine not found.")

    logger.info(f"Deleting washing machine: {machine.name} (UUID: {uuid_str})")

    try:
        db.session.delete(machine)
        db.session.commit()
        logger.info(f"Successfully deleted machine {machine.name} (UUID: {uuid_str})")
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to delete washing machine {uuid_str}: {e}")
        return False


def get_machine_monthly_slots(uuid_str: str, year: int, month: int):
    """
    Returns a structured dictionary of all slots for the given washing machine,
    grouped by date for a specific month and year.

    Args:
        uuid_str (str): UUID of the WashingMachine.
        year (int): Year.
        month (int): Month.

    Returns:
        dict: {date_str: [ {slot_number, time_range, is_booked, booked_by}, ... ]}
    
    Raises:
        ValueError: If no machine is found.
    """
    machine = WashingMachine.query.filter_by(uuid=uuid_str).first()
    if not machine:
        logger.warning(f"No washing machine found with UUID: {uuid_str}")
        raise ValueError("Washing machine not found.")

    logger.info(f"Fetching slots for machine {machine.name} for {year}-{month:02}")

    num_days = calendar.monthrange(year, month)[1]
    result = {}

    # For each day of the month
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        daily_slots = []

        for slot in machine.time_slots:
            booking = Booking.query.filter_by(
                time_slot_id=slot.id,
                date=current_date
            ).first()

            daily_slots.append({
                "slot_number": slot.slot_number,
                "time_range": slot.time_range,
                "is_booked": booking is not None,
                "booked_by": booking.user.fullname if booking else None
            })

        result[str(current_date)] = daily_slots

    logger.info(f"Fetched {len(result)} days of slots for machine {machine.name}")
    return result
