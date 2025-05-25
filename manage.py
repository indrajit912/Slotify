# manage.py
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
# Standard library imports
import sys
import argparse
import getpass
import os
import logging

# Third-party imports
import click
from sqlalchemy import inspect
from flask.cli import FlaskGroup
from flask.cli import with_appcontext

# Local application imports
from app import create_app
from scripts.utils import sha256_hash
from app.extensions import db
from app.models.building import Building
from app.models.course import Course
from app.models.washingmachine import WashingMachine
from app.services import create_user, create_building, create_washing_machine, create_new_course
from config import get_config

cli = FlaskGroup(create_app=create_app)
logger = logging.getLogger(__name__)
bullet_unicode = '\u2022'
app_config = get_config()

def is_db_initialized():
    """
    Check if the database is initialized by checking for existing tables.
    """
    inspector = inspect(db.engine)
    return bool(inspector.get_table_names())

@cli.command("create-superadmin")
@with_appcontext
def create_superadmin():
    """
    Command-line command to create a superadmin user.

    Prompts the user for all necessary details: username, names, email, password, contact number, etc.
    First checks for a secret password to authorize the superadmin creation.
    Also prompts to select an existing Building or create a new one.
    """
    if not is_db_initialized():
        click.echo("❌ Database is not initialized.")
        click.echo("➡️  Please run 'python manage.py setup-db' first to initialize the database.")
        return

    secret_password = getpass.getpass(prompt="Enter the secret password (Indrajit's password): ")
    stored_hash = os.getenv("SUPERADMIN_PASSWORD_HASH")

    if sha256_hash(secret_password) != stored_hash:
        click.echo("❌ Incorrect password. You are not authorized to create a superadmin.")
        return

    click.echo("🔐 Authorization successful. Proceeding to create superadmin.")

    username = click.prompt("Enter username")
    first_name = click.prompt("Enter first name")
    middle_name = click.prompt("Enter middle name", default="", show_default=False)
    last_name = click.prompt("Enter last name", default="", show_default=False)
    email = click.prompt("Enter email address")

    contact_no = click.prompt("Enter contact number", default="", show_default=False)
    room_no = click.prompt("Enter room number", default="", show_default=False)

    password = getpass.getpass(prompt="Enter password: ")
    confirm_password = getpass.getpass(prompt="Confirm password: ")

    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    buildings = Building.query.order_by(Building.name).all()

    if not buildings:
        click.echo("🏢 No buildings found in the system.")
        building_name = click.prompt("Enter the name of the building for the superadmin")
        building_code = click.prompt("Enter the building code (unique short code)")
        building = create_building(name=building_name, code=building_code)
        click.echo(f"✅ Building '{building_name}' created.")
    else:
        click.echo("🏢 Available buildings:")
        for idx, b in enumerate(buildings, start=1):
            click.echo(f"{idx}. {b.name} (Code: {b.code})")
        building_choice = click.prompt("Enter the number of the building", type=int)

        if building_choice < 1 or building_choice > len(buildings):
            click.echo("❌ Invalid choice. Exiting.")
            return

        building = buildings[building_choice - 1]
        click.echo(f"✅ Selected building: {building.name}")

    course = None
    courses = Course.query.order_by(Course.name).all()
    if courses:
        click.echo("🎓 Available courses:")
        for idx, c in enumerate(courses, start=1):
            click.echo(f"{idx}. {c.name}")
        course_choice = click.prompt("Enter the number of the course (or 0 to skip)", type=int, default=0)
        if 1 <= course_choice <= len(courses):
            course = courses[course_choice - 1]
            click.echo(f"✅ Selected course: {course.name}")
        else:
            click.echo("ℹ️ No course selected.")

    try:
        superadmin = create_user(
            username=username,
            first_name=first_name,
            middle_name=middle_name or None,
            last_name=last_name or None,
            email=email,
            password=password,
            role="superadmin",
            contact_no=contact_no or None,
            room_no=room_no or None,
            building_uuid=building.uuid,
            course_uuid=course.uuid if course else None,
        )
        superadmin.email_verified = True
        db.session.commit()
        click.echo(f"🎉 Superadmin created: {superadmin.username} ({superadmin.email})")
    except ValueError as e:
        click.echo(f"❌ Error: {e}")


def create_isi_specific_data():
    """
    Creates ISI-specific initial data:
    - Buildings
    - Washing Machine with time slots
    - Academic courses
    """
    logger.info("Creating ISI-specific initial data...")

    # Create buildings
    building_codes = {
        "Research Scholars' Hostel": "RSH",
        "Hostel 1": "HOS-1",
        "Hostel 2": "HOS-2",
        "Quarter B": "QTR-B",
        "Quarter C": "QTR-C",
        "Quarter D": "QTR-D",
    }

    buildings = {}
    for name, code in building_codes.items():
        try:
            b = create_building(name=name, code=code)
            logger.info(f"Created building: {name} ({code})")
        except ValueError:
            b = Building.query.filter_by(code=code).first()
            logger.warning(f"Building with code {code} already exists.")
        buildings[code] = b

    building = buildings["RSH"]

    # Create washing machine for RSH
    machine = WashingMachine.query.filter_by(code="RSH-BOSCH").first()
    if not machine:
        print("No washing machine with code 'RSH-BOSCH' found.")
        logger.info("No washing machine with code 'RSH-BOSCH' found.")
        print("Preparing to create one with default or custom time slots.")
        logger.info("Preparing to create one with default or custom time slots.")

        _rsh_default_time_slots = [
            {"slot_number": 1, "time_range": "07:00-10:30"},
            {"slot_number": 2, "time_range": "11:30-15:00"},
            {"slot_number": 3, "time_range": "16:00-19:30"},
            {"slot_number": 4, "time_range": "20:30-00:00"}
        ]

        for slot in _rsh_default_time_slots:
            print(f"  Default Slot {slot['slot_number']}: {slot['time_range']}")

        choice = input("Use default time slots? (y/n): ").strip().lower()
        if choice == 'n':
            custom_slots = []
            print("Enter custom time slots in the format HH:MM-HH:MM.")
            print("Type 'done' when finished.\n")
            slot_number = 1
            while True:
                user_input = input(f"  Time range for slot {slot_number}: ").strip()
                if user_input.lower() == "done":
                    break
                # Optional: Validate time format here
                custom_slots.append({
                    "slot_number": slot_number,
                    "time_range": user_input
                })
                slot_number += 1
            time_slots = custom_slots
        else:
            time_slots = _rsh_default_time_slots

        new_machine = create_washing_machine(
            name="BOSCH Front Loaded Machine",
            code="RSH-BOSCH",
            building_uuid=building.uuid,
            time_slots=time_slots
        )
        logger.info(f"Washing machine '{new_machine.name}' created at RSH.")
        print(f"Washing machine '{new_machine.name}' created at RSH.")
    else:
        logger.warning("Washing machine 'RSH-BOSCH' already exists.")
        print("Washing machine 'RSH-BOSCH' already exists.")

    # Create courses
    course_data = [
        ("PHD-MATH", "Doctor of Philosophy in Mathematics", "PhD", "Stat-Math Unit", "PhD Math", 5, "Doctoral programme in pure mathematics"),
        ("PHD-LIS", "Doctor of Philosophy in Library Science", "PhD", "Documentation Research And Training Centre", "PhD Library Sc.", 5, "Doctoral programme in Library Science"),
        ("PHD-AS", "Doctor of Philosophy in Applied Statistics", "PhD", "Applied Statistics Unit", "PhD Applied Stat", 5, "Doctoral programme in Applied Statistics"),
        ("PHD-CS", "Doctor of Philosophy in Computer Science", "PhD", "System Science and Informatics Unit", "PhD Computer Sc", 5, "Doctoral programme in Computer Science"),
        ("PHD-PHYS", "Doctor of Philosophy in Physics", "PhD", "System Science and Informatics Unit", "PhD Physics", 5, "Doctoral programme in Physics"),
        ("PHD-ECA", "Doctor of Philosophy in Economics", "PhD", "Economic Analysis Unit", "PhD Economics", 5, "Doctoral programme in Economics"),
        ("MS-QMS", "Master of Science in Quality Management Science", "PG", "Statistical Quality Control & Operations Research Unit", "MSc Quality Management Sc", 1, ""),
        ("MS-LIS", "Master of Science in Library & Information Science", "PG", "Documentation Research And Training Centre", "MSc Library Sc", 2, ""),
        ("BMATH", "Bachelor of Mathematics (Hons.)", "UG", "Stat-Math Unit", "B-Math", 3, ""),
        ("MMATH", "Master of Mathematics", "PG", "Stat-Math Unit", "M-Math", 2, ""),
        ("BSDS", "Bachelor of Statistical Data Science (Hons.)", "UG", "Stat-Math Unit", "B-SDS", 4, "")
    ]

    for code, name, level, dept, short_name, duration, desc in course_data:
        try:
            create_new_course(code=code, name=name, level=level, department=dept,
                              short_name=short_name, duration_years=duration, description=desc)
            logger.info(f"Course created: {code} - {name}")
            print(f"Course created: {code} - {name}")
        except ValueError:
            logger.warning(f"Course with code {code} already exists.")
            print(f"Course with code {code} already exists.")

    logger.info("ISI-specific data initialization complete.") 
    print("ISI-specific data initialization complete.")

@cli.command("setup-db")
@click.option('--isi', is_flag=True, default=False, help="Create ISI specific data after setup")
@with_appcontext
def setup_database(isi):
    """
    Command-line utility to set up the database.

    This command checks whether the database has already been initialized
    using is_db_initialized(). If it has, the user is prompted whether to
    delete and recreate it from scratch.

    Usage:
        python manage.py setup-db [--isi]

    Args:
        isi (bool): If True, create ISI specific data after database setup.

    Returns:
        None
    """
    db_path = app_config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")

    if is_db_initialized():
        click.echo("[!] Database appears to already be initialized.")
        if not click.confirm("Do you want to delete the existing database and start fresh?"):
            click.echo("Aborted. Database remains unchanged.")
            return
        os.remove(db_path)
        click.echo("[-] Existing database deleted.")

    db.create_all()
    click.echo("[-] Database tables created successfully.")

    if not app_config.APP_DATA_DIR.exists():
        app_config.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        click.echo("[-] '/app_data' directory created successfully.")

    if isi:
        click.echo("[*] Creating ISI specific data...")
        create_isi_specific_data()
        click.echo("[+] ISI specific data created successfully.")


def help_command():
    """
    Command-line utility to display help information about available commands.

    Usage:
        python manage.py help

    Returns:
        None
    """
    print("Available commands:")
    print("1. setup-db: Set up the database.")


if __name__ == '__main__':
    cli()