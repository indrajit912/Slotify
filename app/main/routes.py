"""
app/main/routes.py

This module defines the routes and views for the Flask web application.

Author: Indrajit Ghosh
Created on: May 10, 2025
"""
import logging
import calendar
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from . import main_bp
from app.models.washingmachine import WashingMachine
from app.models.booking import TimeSlot
from app.services import get_machine_monthly_slots, book_slot, cancel_booking

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
    

@main_bp.route('/book-slot', methods=['POST'])
@login_required
def book_slot_route():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    machine_id = data.get('machine_id')
    slot_number = data.get('slot_number')
    date_str = data.get('date')
    if not (machine_id and slot_number and date_str):
        return jsonify({'success': False, 'message': 'Missing parameters'}), 400
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format'}), 400

    # Query slot_uuid by machine_id and slot_number
    slot = TimeSlot.query.filter_by(machine_id=machine_id, slot_number=slot_number).first()
    if not slot:
        return jsonify({'success': False, 'message': 'Slot not found'}), 404
    
    try:
        booking = book_slot(str(current_user.uuid), slot.uuid, date_obj)
        return jsonify({'success': True, 'message': 'Booking successful!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 409
    

@main_bp.route('/cancel-slot', methods=['POST'])
@login_required
def cancel_slot_route():
    data = request.get_json()

    slot_uuid = data.get('slot_uuid')
    date_str = data.get('date')

    if not slot_uuid or not date_str:
        return jsonify({'success': False, 'message': 'Invalid request data.'}), 400

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format.'}), 400

    success = cancel_booking(user_uuid=current_user.uuid, slot_uuid=slot_uuid, day=date_obj)
    if success:
        return jsonify({'success': True, 'message': 'Slot cancelled successfully.'})
    else:
        return jsonify({'success': False, 'message': 'You cannot cancel this slot.'})

