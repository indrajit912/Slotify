# manage.py
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
# Standard library imports
import sys
import argparse
import json
import os
import logging

# Third-party imports
import requests
from cryptography.fernet import Fernet
from flask import current_app
from flask.cli import FlaskGroup
from tabulate import tabulate

# Local application imports
from app import create_app
from config import Config
from app.extensions import db
from app.models.user import User
from app.models.washingmachine import WashingMachine

cli = FlaskGroup(create_app=create_app)
logger = logging.getLogger(__name__)
bullet_unicode = '\u2022'


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