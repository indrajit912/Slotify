# scripts/export_import.py
# Author: Indrajit Ghosh
# Created On: May 28, 2025
# 
import json
from pathlib import Path
from datetime import datetime

from app.models.building import Building
from app.models.course import Course
from app.models.user import User, CurrentEnrolledStudent
from app.models.washingmachine import WashingMachine
from app.models.booking import Booking, TimeSlot
from app.utils.data_io import export_model_data, import_model_data, EXPORT_DIR, IMPORT_DIR

def export_all_json(session, save: bool = False):
    """
    Export all model data to a single JSON file or return as a dictionary.

    Args:
        session: SQLAlchemy session.
        save (bool): If True, writes data to slotify_db_<timestamp>.json. Else, returns a dict.

    Returns:
        Path | dict: Path to JSON file if save=True; otherwise the data as a dict.
    """
    data = {
        "buildings": export_model_data(session, Building, "buildings.json", save=False),
        "courses": export_model_data(session, Course, "courses.json", save=False),
        "current_enrolled_students": export_model_data(session, CurrentEnrolledStudent, "current_enrolled_students.json", save=False),
        "users": export_model_data(session, User, "users.json", save=False),
        "machines": export_model_data(session, WashingMachine, "machines.json", save=False),
        "bookings": export_model_data(session, Booking, "bookings.json", save=False),
        "timeslots": export_model_data(session, TimeSlot, "timeslots.json", save=False),
    }

    if save:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        json_path = EXPORT_DIR / f"slotify_db_{timestamp}.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Exported to: {json_path}")
        return json_path

    return data

def import_all_json(session, json_file_path):
    """
    Import all Slotify data from a single JSON file containing all models' data.

    Args:
        session (Session): SQLAlchemy session.
        json_file_path (Path or str): Path to the JSON file with all data.

    Returns:
        None. Prints import summary for each model.

    Raises:
        FileNotFoundError: If the JSON file is not found.
    """
    json_file_path = Path(json_file_path)
    if not json_file_path.exists():
        raise FileNotFoundError(f"{json_file_path} not found.")

    with json_file_path.open(encoding="utf-8") as f:
        data = json.load(f)

    print(import_model_data(session, data, CurrentEnrolledStudent.from_json, key="current_enrolled_students"))

    print(import_model_data(session, data, Building.from_json, key="buildings"))
    building_lookup = {b.uuid: b for b in Building.query.all()}

    print(import_model_data(session, data, Course.from_json, key="courses"))
    course_lookup = {c.uuid: c for c in Course.query.all()}

    print(import_model_data(session, data, WashingMachine.from_json, key="machines", building_lookup=building_lookup))
    machine_lookup = {wm.uuid: wm for wm in WashingMachine.query.all()}

    print(import_model_data(session, data, User.from_json, key="users", building_lookup=building_lookup, course_lookup=course_lookup))
    user_lookup = {u.uuid: u for u in User.query.all()}

    print(import_model_data(session, data, TimeSlot.from_json, key="timeslots", machine_lookup=machine_lookup))
    time_slot_lookup = {ts.uuid: ts for ts in TimeSlot.query.all()}

    print(import_model_data(session, data, Booking.from_json, key="bookings", user_lookup=user_lookup, time_slot_lookup=time_slot_lookup))

    print(f"✅ Import completed from {json_file_path}")
