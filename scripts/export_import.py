# scripts/export_import.py
# Author: Indrajit Ghosh
# Created On: May 28, 2025
# 
import shutil
import zipfile
from datetime import datetime

from app.models.building import Building
from app.models.course import Course
from app.models.user import User, CurrentEnrolledStudent
from app.models.washingmachine import WashingMachine
from app.models.booking import Booking, TimeSlot
from app.utils.data_io import export_model_data, import_model_data, EXPORT_DIR, IMPORT_DIR

def export_all_zipped(session):
    # Format current timestamp
    timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    zip_name = f"slotify_db_{timestamp}"
    temp_dir = EXPORT_DIR / zip_name
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Export all JSON files into the temp dir
    export_model_data(session, Building, temp_dir / "buildings.json")
    export_model_data(session, Course, temp_dir / "courses.json")
    export_model_data(session, CurrentEnrolledStudent, temp_dir / "current_enrolled_students.json")
    export_model_data(session, User, temp_dir / "users.json")
    export_model_data(session, WashingMachine, temp_dir / "machines.json")
    export_model_data(session, Booking, temp_dir / "bookings.json")
    export_model_data(session, TimeSlot, temp_dir / "timeslots.json")

    # Zip the directory
    zip_path = EXPORT_DIR / f"{zip_name}.zip"
    shutil.make_archive(zip_path.with_suffix(""), 'zip', temp_dir)

    # Cleanup temporary directory
    shutil.rmtree(temp_dir)

    print(f"✅ Exported and zipped to: {zip_path}")
    return zip_path

def import_all_zipped(session, zip_file_path):
    # Create an extract directory with timestamp
    timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
    extract_dir = IMPORT_DIR / f"slotify_import_{timestamp}"
    extract_dir.mkdir(parents=True, exist_ok=True)

    # Extract the zip
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    # Call import_model_data with paths in extract_dir
    print(import_model_data(session, extract_dir / "current_enrolled_students.json", CurrentEnrolledStudent.from_json))

    print(import_model_data(session, extract_dir / "buildings.json", Building.from_json))
    building_lookup = {b.uuid: b for b in Building.query.all()}

    print(import_model_data(session, extract_dir / "courses.json", Course.from_json))
    course_lookup = {c.uuid: c for c in Course.query.all()}

    print(import_model_data(session, extract_dir / "machines.json", WashingMachine.from_json, building_lookup=building_lookup))
    machine_lookup = {wm.uuid: wm for wm in WashingMachine.query.all()}

    print(import_model_data(session, extract_dir / "users.json", User.from_json, building_lookup=building_lookup, course_lookup=course_lookup))
    user_lookup = {u.uuid: u for u in User.query.all()}

    print(import_model_data(session, extract_dir / "timeslots.json", TimeSlot.from_json, machine_lookup=machine_lookup))
    time_slot_lookup = {ts.uuid: ts for ts in TimeSlot.query.all()}

    print(import_model_data(session, extract_dir / "bookings.json", Booking.from_json, user_lookup=user_lookup, time_slot_lookup=time_slot_lookup))

    # Cleanup
    shutil.rmtree(extract_dir)
    print(f"✅ Import completed and cleaned up: {extract_dir}")