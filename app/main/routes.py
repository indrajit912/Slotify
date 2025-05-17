"""
app/main/routes.py

This module defines the routes and views for the Flask web application.

Author: Indrajit Ghosh
Created on: May 10, 2025
"""
import logging
import calendar

from flask import render_template, request, redirect, url_for, flash

from . import main_bp
from app.models.washingmachine import WashingMachine
from app.services import get_machine_monthly_slots

logger = logging.getLogger(__name__)


#######################################################
#                      Homepage
#######################################################
@main_bp.route('/')
def index():
    logger.info("Visited homepage.")
    return render_template("index.html")


@main_bp.route('/machine/<uuid_str>/calendar/<int:year>/<int:month>')
def view_machine_calendar(uuid_str, year, month):
    """
    View the monthly booking chart for a specific washing machine.
    """
    try:
        machine = WashingMachine.query.filter_by(uuid=uuid_str).first_or_404()
        calendar_data = get_machine_monthly_slots(uuid_str, year, month)
        month_name = calendar.month_name[month]  # Convert 5 to 'May'
        return render_template('machine_calendar.html',
                               machine=machine,
                               calendar_data=calendar_data,
                               year=year,
                               month=month_name)  # Pass name instead of number
    except ValueError:
        flash("Washing machine not found.", "danger")
        return redirect(url_for("main.index"))
