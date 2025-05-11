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
from flask import current_app
from flask.cli import FlaskGroup

# Local application imports
from app import create_app
from config import Config
from scripts.utils import sha256_hash
from app.extensions import db
from app.models.building import Building
from app.services import create_user, create_building

cli = FlaskGroup(create_app=create_app)
logger = logging.getLogger(__name__)
bullet_unicode = '\u2022'

@cli.command("create-superadmin")
def create_superadmin():
    """
    Command-line command to create a superadmin user.
    
    Prompts the user for all necessary details: username, fullname, email, and password.
    First, checks for a secret password to authorize the superadmin creation.
    """
    # Ask for the secret password to proceed with superadmin creation
    secret_password = getpass.getpass(prompt="Enter the secret password (Indrajit's password): ")

    # Retrieve the stored secret password hash from .env
    stored_hash = os.getenv("SUPERADMIN_PASSWORD_HASH")

    # Hash the entered password and compare it to the stored hash
    if sha256_hash(secret_password) != stored_hash:
        click.echo("Error: Incorrect password. You are not authorized to create a superadmin.")
        return

    click.echo("You are about to create a superadmin. This operation requires authorization.")

    # Prompt for the user's information
    username = click.prompt("Enter username")
    fullname = click.prompt("Enter full name")
    email = click.prompt("Enter email address")
    
    # Ask for the password securely using getpass
    password = getpass.getpass(prompt="Enter password: ")

    # Get all buildings from the database
    buildings = Building.query.all()

    if not buildings:
        click.echo("No buildings found in the system. You need to create a new building for the superadmin.")
        building_name = click.prompt("Enter the name of the building where the superadmin resides (e.g. Hostel 1, RS Hostel)")

        # Create the building and associate it with the superadmin
        building = create_building(name=building_name)

        click.echo(f"New building '{building_name}' created and assigned to the superadmin.")
        building_uuid = building.uuid
    else:
        # If buildings exist, allow the superadmin to choose one
        click.echo("Please select a building from the list of available buildings:")

        for idx, b in enumerate(buildings, 1):
            click.echo(f"{idx}. {b.name} (UUID: {b.uuid})")

        building_choice = click.prompt("Enter the number of the building you want to assign to the superadmin", type=int)
        
        if building_choice < 1 or building_choice > len(buildings):
            click.echo("Invalid choice. Exiting.")
            return
        
        building_uuid = buildings[building_choice - 1].uuid
        click.echo(f"Building {buildings[building_choice - 1].name} (UUID: {building_uuid}) selected for the superadmin.")

    try:
        # Create the superadmin using the service function
        superadmin = create_user(username, fullname, email, password, role="superadmin", building_uuid=building_uuid)
        superadmin.email_verified = True
        click.echo(f"Superadmin created: {superadmin.username} ({superadmin.email})")
    except ValueError as e:
        click.echo(f"Error: {e}")



@cli.command("setup-db")
def setup_database():
    """
    Command-line utility to set up the database.

    This command creates all necessary tables in the database based on defined models.

    Usage:
        flask setup_database

    Returns:
        None
    """
    with current_app.app_context():
        db.create_all()
        print("[-] Database tables created successfully!")

        # Create APP_DATA dir
        if not Config.APP_DATA_DIR.exists():
            Config.APP_DATA_DIR.mkdir()
            print("[-] '/app_data' directory created successfully!")

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