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
from app.services import create_user, create_building
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
    
    Prompts the user for all necessary details: username, fullname, email, and password.
    First, checks for a secret password to authorize the superadmin creation.
    """
    if not is_db_initialized():
        click.echo("❌ Database is not initialized.")
        click.echo("➡️  Please run 'python manage.py create-db' first to initialize the database.")
        return

    secret_password = getpass.getpass(prompt="Enter the secret password (Indrajit's password): ")
    stored_hash = os.getenv("SUPERADMIN_PASSWORD_HASH")

    if sha256_hash(secret_password) != stored_hash:
        click.echo("❌ Incorrect password. You are not authorized to create a superadmin.")
        return

    click.echo("🔐 Authorization successful. Proceeding to create superadmin.")

    username = click.prompt("Enter username")
    fullname = click.prompt("Enter full name")
    email = click.prompt("Enter email address")
    password = getpass.getpass(prompt="Enter password: ")

    buildings = Building.query.all()

    if not buildings:
        click.echo("🏢 No buildings found in the system.")
        building_name = click.prompt("Enter the name of the building for the superadmin")
        building = create_building(name=building_name)
        click.echo(f"✅ Building '{building_name}' created.")
        building_uuid = building.uuid
    else:
        click.echo("🏢 Available buildings:")
        for idx, b in enumerate(buildings, 1):
            click.echo(f"{idx}. {b.name} (UUID: {b.uuid})")
        building_choice = click.prompt("Enter the number of the building", type=int)

        if building_choice < 1 or building_choice > len(buildings):
            click.echo("❌ Invalid choice. Exiting.")
            return

        building_uuid = buildings[building_choice - 1].uuid
        click.echo(f"✅ Selected building: {buildings[building_choice - 1].name}")

    try:
        superadmin = create_user(username, fullname, email, password, role="superadmin", building_uuid=building_uuid)
        superadmin.email_verified = True
        click.echo(f"🎉 Superadmin created: {superadmin.username} ({superadmin.email})")
    except ValueError as e:
        click.echo(f"❌ Error: {e}")


@cli.command("setup-db")
@with_appcontext
def setup_database():
    """
    Command-line utility to set up the database.

    This command checks whether the database has already been initialized
    using is_db_initialized(). If it has, the user is prompted whether to
    delete and recreate it from scratch.

    Usage:
        flask setup-db

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
    parser = argparse.ArgumentParser(description='Command-line utility for managing Slotify.')
    parser.add_argument('command', type=str, nargs='?', help='Command to execute (e.g., setup-db, help)')
    args = parser.parse_args()

    if args.command == 'help':
        help_command()
    elif args.command:
        sys.argv = ['manage.py', args.command]  # Modify sys.argv to include the command
        cli.main()  # Use cli.main() to execute the command
    else:
        print("Please provide a valid command. Use 'python manage.py help' to see available commands.")