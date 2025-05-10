# slotify.py
#
# Author: Indrajit Ghosh
# Created on: May 10, 2025
#
"""
This script starts the Flask development server to run the web application.

Usage:
    - Run the Flask development server:
    >>> flask run

    - Run the gunicorn server
    >>> /env/bin/gunicorn --bind 0.0.0.0:5000 run:app

Database initialization:
    1. To setup the database for the first time use the following command
on the terminal:

    $ env/bin/python manage.py setup_db

    OR, you can do it manually by the following set of commands on Flask Shell
    $ flask shell
        >>> from app import db
        >>> from app.models.models import *
        >>> db.create_all()

    2. Use the following to run the app locally:
    $ flask run

Note: Flask Migration
    1. flask db init
    2. flask db migrate -m 'Initial Migrate'
    3. flask db upgrade
    These 2 and 3 you need to do everytime you change some in your db!
"""

from app import create_app

app = create_app()
