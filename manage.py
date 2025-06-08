# manage.py
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
# Standard library imports
import getpass
import os
import logging

# Third-party imports
import click
from sqlalchemy import inspect
from flask.cli import FlaskGroup
from flask.cli import with_appcontext
from flask_migrate import upgrade

# Local application imports
from app import create_app
from scripts.utils import sha256_hash
from app.extensions import db
from app.models.building import Building
from app.models.course import Course
from app.services import create_user, create_building

cli = FlaskGroup(create_app=create_app)

logger = logging.getLogger(__name__)

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
        click.echo("➡️  Please run 'flask deploy' first to initialize the database.")
        return

    secret_password = getpass.getpass(prompt="Enter the secret password (Indrajit's password): ")
    stored_hash = os.getenv("SUPERADMIN_CREATION_PASSWORD_HASH")

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


@cli.command("deploy")
def deploy():
    """Run deployment tasks."""  
    # migrate database to latest revision
    upgrade()

if __name__ == '__main__':
    cli()