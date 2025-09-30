"""
app/main/routes.py

This module defines the routes and views for the Flask web application.

Author: Indrajit Ghosh
Created on: May 10, 2025
"""
import logging
import base64
import io
import calendar
from datetime import datetime, date

import qrcode
from flask import render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required, current_user

from . import main_bp
from app.models.washingmachine import WashingMachine
from app.models.booking import TimeSlot
from app.services import get_machine_monthly_slots, book_slot, cancel_booking, get_all_admins
from app.utils.decorators import admin_required
from config import Config

logger = logging.getLogger(__name__)


#######################################################
#                      Homepage
#######################################################
@main_bp.route('/')
def index():
    logger.info("Visited homepage.")

    if current_app.config.get("MAINTENANCE_MODE", False):
        return render_template("maintenance.html"), 503

    return render_template("index.html")
    

@main_bp.route('/view-all-admins')
def view_all_admins():
    admins = get_all_admins()
    return render_template('view_all_admins.html', admins=admins)


@main_bp.route('/machine/<uuid_str>/calendar/<int:year>/<int:month>')
def view_machine_calendar(uuid_str, year, month):
    """
    View the monthly booking chart for a specific washing machine.
    Only admin can view past months.
    Unauthenticated users have same restrictions as non-admin.
    """
    try:
        machine = WashingMachine.query.filter_by(uuid=uuid_str).first_or_404()

        today = date.today()
        is_past_month = (year < today.year) or (year == today.year and month < today.month)

        # Determine if user is admin, else treat as not admin (including unauthenticated)
        is_admin = current_user.is_authenticated and current_user.is_admin()
        not_admin = not is_admin

        # Restrict past calendar view to admins only
        if is_past_month and not_admin:
            flash("You are not authorized to view past calendars.", "warning")
            return redirect(url_for("auth.dashboard"))

        calendar_data = get_machine_monthly_slots(
            uuid_str=uuid_str,
            year=year,
            month=month,
            exclude_past=not_admin
        )

        month_name = calendar.month_name[month]  # Convert 5 to 'May'

        return render_template('machine_calendar.html',
                               machine=machine,
                               calendar_data=calendar_data,
                               year=year,
                               month=month_name,
                               month_num=month)

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
    
    # Fetch machine and check availability
    machine = WashingMachine.query.get(machine_id)
    if not machine:
        return jsonify({'success': False, 'message': 'Washing machine not found'}), 404

    if not machine.is_available():
        return jsonify({'success': False, 'message': 'Machine is not available for booking'}), 403
    
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

    try:
        success = cancel_booking(user_uuid=current_user.uuid, slot_uuid=slot_uuid, day=date_obj)
        return jsonify({'success': True, 'message': 'Slot cancelled successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@main_bp.route('/machine/calendar/qrcode', methods=['POST'])
@admin_required
def generate_machine_calendar_qr():
    app_dir = Config.APP_DATA_DIR
    uuid_str = request.form.get('uuid_str')
    year = int(request.form.get('year'))
    month = int(request.form.get('month'))

    machine = WashingMachine.query.filter_by(uuid=uuid_str).first_or_404()
    building = machine.building

    calendar_url = url_for(
        'main.view_machine_calendar',
        uuid_str=uuid_str,
        year=year,
        month=month,
        _external=True
    )

    qr_img = qrcode.make(calendar_url)
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template(
        'machine_qr.html',
        machine=machine,
        building=building,
        qr_b64=qr_b64,
        current_year=datetime.now().year
    )


@main_bp.route('/dev/error/<int:code>')
def dev_error(code):
    """
    Test route to manually trigger error pages.

    Supported codes:
        401 - Unauthorized
        403 - Forbidden
        404 - Not Found
        422 - Unprocessable Entity
        500 - Internal Server Error

    Example usage:
        /dev/error/403
    """
    if code == 401:
        abort(401)
    elif code == 403:
        abort(403)
    elif code == 404:
        abort(404)
    elif code == 422:
        abort(422)
    elif code == 500:
        # This triggers the 500 error page by causing an exception
        raise Exception("Simulated server error for 500 page test.")
    else:
        return f"Unsupported error code {code}. Try 401, 403, 404, 422, or 500."
    
