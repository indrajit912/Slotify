# app/services/washing_machine_service.py
#
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
import logging
import calendar
from datetime import date

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import extract

from app.models.washingmachine import WashingMachine
from app.models.booking import TimeSlot, Booking
from app.models.building import Building
from app.services.building_service import get_building_by_uuid
from app.extensions import db
from scripts.utils import utcnow

logger = logging.getLogger(__name__)

from app.utils.image_utils import save_machine_image
from werkzeug.datastructures import FileStorage

def create_washing_machine(
    name: str,
    code: str,
    building_uuid: str,
    time_slots: list[dict],
    image_file: FileStorage = None,
    image_url: str = None
):
    """
    Creates a new washing machine with optional image and associated time slots.

    Args:
        name (str): Name of the washing machine.
        code (str): Unique code for the washing machine.
        building_uuid (str): UUID of the building where the machine is located.
        time_slots (list of dict): Each dict should have 'slot_number' and 'time_range'.
        image_file (FileStorage, optional): Optional uploaded image file.
        image_url (str, optional): Optional direct URL to an image (e.g., Google Drive or Dropbox).

    Returns:
        WashingMachine: The created machine object.

    Raises:
        ValueError: If the machine name or code already exists or building is not found.
    """
    if WashingMachine.query.filter((WashingMachine.name == name) | (WashingMachine.code == code)).first():
        logger.warning(f"WashingMachine name or code already exists: name='{name}', code='{code}'")
        raise ValueError("Washing machine name or code already exists.")

    building = Building.query.filter_by(uuid=building_uuid).first()
    if not building:
        logger.error(f"Building not found with UUID: {building_uuid}")
        raise ValueError(f"No building found with UUID: {building_uuid}")

    # Create machine
    machine = WashingMachine(name=name, code=code, building=building)
    db.session.add(machine)
    db.session.flush()  # Ensures machine.id is available before adding related time slots

    # Save time slots
    for slot in time_slots:
        ts = TimeSlot(
            machine_id=machine.id,
            slot_number=slot["slot_number"],
            time_range=slot["time_range"]
        )
        ts.update_hours_from_range()
        db.session.add(ts)

    # Handle image upload
    if image_file:
        try:
            image_path = save_machine_image(image_file, machine.uuid)
            if image_path:
                machine.image_path = image_path
        except Exception as e:
            logger.warning(f"Failed to save image for machine '{name}': {e}")
    elif image_url:
        machine.image_url = image_url.strip()

    try:
        db.session.commit()
        logger.info(f"WashingMachine '{name}' created in building '{building.name}' with {len(time_slots)} slots.")
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Failed to create machine '{name}' in building '{building.name}': {e}")
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

def update_washing_machine(machine_uuid: str, **kwargs):
    """
    Update the details of a washing machine by its UUID.
    
    Args:
        machine_uuid (str): UUID of the washing machine to update.
        kwargs: Fields to update. Supported keys: 'name', 'code', 'building_uuid', 'status',
                'image_file' (FileStorage), 'image_url' (str).
        
    Returns:
        WashingMachine: The updated washing machine object.
    
    Raises:
        ValueError: If no washing machine is found with the provided UUID or if
                    new name/code conflicts with existing machines.
    """
    try:
        # Find the washing machine by UUID
        washing_machine = db.session.query(WashingMachine).filter_by(uuid=machine_uuid).first()
        
        if not washing_machine:
            logger.error(f"Washing machine with UUID {machine_uuid} not found.")
            raise ValueError(f"No washing machine found with UUID: {machine_uuid}")
        
        logger.info(f"Updating washing machine {washing_machine.name} (UUID: {machine_uuid})")

        # Update 'name' with uniqueness check
        if 'name' in kwargs:
            new_name = kwargs['name']
            existing_name = WashingMachine.query.filter(WashingMachine.name == new_name, WashingMachine.uuid != machine_uuid).first()
            if existing_name:
                raise ValueError(f"Washing machine name '{new_name}' already exists.")
            washing_machine.name = new_name

        # Update 'code' with uniqueness check
        if 'code' in kwargs:
            new_code = kwargs['code']
            existing_code = WashingMachine.query.filter(WashingMachine.code == new_code, WashingMachine.uuid != machine_uuid).first()
            if existing_code:
                raise ValueError(f"Washing machine code '{new_code}' already exists.")
            washing_machine.code = new_code

        # Update building if 'building_uuid' given
        if 'building_uuid' in kwargs:
            new_building_uuid = kwargs['building_uuid']
            new_building = get_building_by_uuid(new_building_uuid)
            if not new_building:
                raise ValueError(f"No building found with UUID: {new_building_uuid}")
            washing_machine.building = new_building
        
        # Update status if 'status' given
        if 'status' in kwargs:
            washing_machine.status = kwargs['status']

        # Handle image update
        image_file = kwargs.get("image_file")
        image_url = kwargs.get("image_url")

        if image_file:
            try:
                image_path = save_machine_image(image_file, washing_machine.uuid)
                if image_path:
                    washing_machine.image_path = image_path
                    washing_machine.image_url = None  # Clear URL if uploading new file
            except Exception as e:
                logger.warning(f"Failed to save new image file for machine '{washing_machine.name}': {e}")

        elif image_url:
            washing_machine.image_url = image_url.strip()
            washing_machine.image_path = None  # Clear path if using URL

        # If any changes were made
        if kwargs:
            washing_machine.last_updated = utcnow()

        try:
            db.session.commit()
            logger.info(f"Washing machine with UUID {machine_uuid} updated successfully.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating washing machine (UUID: {machine_uuid}): {e}")
            raise ValueError("Could not update washing machine.")

        return washing_machine

    except ValueError as ve:
        logger.error(f"Error updating washing machine: {ve}")
        raise ve
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error while updating washing machine: {str(e)}")
        raise Exception("An error occurred while updating the washing machine. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise Exception("An unexpected error occurred. Please try again.")


def get_machine_monthly_slots(uuid_str: str, year: int, month: int, exclude_past: bool = False):
    """
    Returns a structured dictionary of all slots for the given washing machine,
    grouped by date for a specific month and year.

    Args:
        uuid_str (str): UUID of the WashingMachine.
        year (int): Year.
        month (int): Month.
        exclude_past (bool): If True, exclude slots for past dates.

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
    today = date.today()

    # For each day of the month
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)

        if exclude_past and current_date < today:
            continue  # skip past dates

        daily_slots = []

        for slot in machine.time_slots:
            booking = Booking.query.filter_by(
                time_slot_id=slot.id,
                date=current_date
            ).first()

            daily_slots.append({
                "slot_number": slot.slot_number,
                "slot_uuid": slot.uuid,
                "time_range": slot.time_range,
                "is_booked": booking is not None,
                "booked_by": {
                    "user_uuid": booking.user.uuid,
                    "fullname": booking.user.fullname,
                    "first_tname": booking.user.first_name,
                    "username": booking.user.username[:15],
                    "email": booking.user.email,
                    "room_no": booking.user.room_no,
                    "contact_no": booking.user.contact_no,
                    "avatar": booking.user.avatar(size=120),
                    "course": booking.user.course.short_name if not booking.user.is_guest() else 'Guest',
                    "building": booking.user.building.name if booking.user.building else "N/A"
                } if booking else None
            })

        result[str(current_date)] = daily_slots

    logger.info(f"Fetched {len(result)} days of slots for machine {machine.name}")
    return result