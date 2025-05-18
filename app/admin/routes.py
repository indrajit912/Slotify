# app/admin/routes.py
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#

# Standard library imports
import logging

# Third-party imports
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import desc

# Local application imports
from . import admin_bp
from app.models.user import User
from app.models.washingmachine import WashingMachine
from app.models.building import Building
from app.utils.decorators import admin_required
from app.services import create_washing_machine, create_building, update_user_by_uuid, delete_user_by_uuid, get_user_by_uuid

logger = logging.getLogger(__name__)

@admin_bp.route('/')
@admin_required
def home():
    # Retrieve all users and buildings from the database
    users = User.query.order_by(desc(User.date_joined)).all()
    buildings = Building.query.all()

    logger.info(f"Admin dashboard visited by the admin '{current_user.email}'.")

    return render_template(
        'admin.html', 
        users=users,
        buildings=buildings
    )


@admin_bp.route('/admins')
@admin_required
def view_admins():
    """View all users with role admin or superadmin."""
    admins = User.query.filter(User.role.in_(['admin', 'superadmin'])).order_by(desc(User.date_joined)).all()
    logger.info(f"Admin '{current_user.email}' viewed all admins.")
    return render_template('view_admins.html', admins=admins)


@admin_bp.route('/users')
@admin_required
def view_users():
    """View all non-admin users."""
    users = User.query.filter(User.role == 'user').order_by(desc(User.date_joined)).all()
    logger.info(f"Admin '{current_user.email}' viewed all users.")
    return render_template('view_users.html', users=users)


@admin_bp.route('/machines')
@admin_required
def view_machines():
    """View all washing machines."""
    machines = WashingMachine.query.order_by(desc(WashingMachine.created_at)).all()
    logger.info(f"Admin '{current_user.email}' viewed all washing machines.")
    return render_template('view_machines.html', machines=machines)

@admin_bp.route('/create_building_route', methods=['POST'])
@admin_required
def create_building_route():
    building_name = request.form.get('building_name')
    building_code = request.form.get('building_code')
    try:
        new_building = create_building(name=building_name, code=building_code)
        flash(f"Building '{new_building.name}({building_code})' created successfully!", "success")
        return redirect(url_for('admin.home'))  # Redirect back to the admin dashboard
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for('admin.home'))
    
@admin_bp.route('/create_machine', methods=['POST'])
@admin_required
def create_machine():
    """
    Handle the form submission for creating a new washing machine with time slots.
    """
    try:
        # Get washing machine name from form
        machine_name = request.form.get('machine_name')
        machine_code = request.form.get('machine_code')
        machine_building_uuid = request.form.get('machine_building_uuid')
        
        # Get time slots from the form
        time_slots = []
        slot_numbers = request.form.getlist('slot_number')
        time_ranges = request.form.getlist('time_range')
        
        # Build the time slot list
        for slot_number, time_range in zip(slot_numbers, time_ranges):
            time_slots.append({
                'slot_number': int(slot_number),
                'time_range': time_range
            })

        # Call the function to create washing machine with time slots
        new_machine = create_washing_machine(
            name=machine_name,
            code=machine_code,
            building_uuid=machine_building_uuid,
            time_slots=time_slots
        )

        # Flash success message and redirect
        flash(f"Washing machine '{new_machine.name}' created successfully!", "success")
        return redirect(url_for('admin.view_machines'))

    except Exception as e:
        logger.error(f"Error creating washing machine: {str(e)}")
        flash("An error occurred while creating the washing machine. Please try again.", "danger")
        return redirect(url_for('admin.home'))
    

@admin_bp.route('/make_admin/<user_uuid>', methods=['POST'])
@admin_required
def make_admin(user_uuid):
    user = get_user_by_uuid(user_uuid)
    current_admin = current_user

    if not user:
        flash('User not found.', 'danger')
        logger.warning(f"[{current_admin.username}] tried to make a non-existent user ({user_uuid}) an admin.")
    elif user.is_admin():
        flash(f'{user.username} is already an admin.', 'info')
        logger.info(f"[{current_admin.username}] attempted to make {user.username} an admin, but they already are.")
    else:
        update_user_by_uuid(user_uuid, role='admin')
        flash(f'Admin privileges granted to {user.username}.', 'success')
        logger.info(f"[{current_admin.username}] granted admin privileges to {user.username}.")

    return redirect(url_for('admin.view_users'))


@admin_bp.route('/revoke_admin/<user_uuid>', methods=['POST'])
@admin_required
def revoke_admin(user_uuid):
    user = get_user_by_uuid(user_uuid)
    current_admin = current_user

    if not user:
        flash('User not found.', 'danger')
        logger.warning(f"[{current_admin.username}] tried to revoke admin of non-existent user ({user_uuid}).")
    elif user.is_superadmin():
        flash('You cannot revoke admin privileges from a superadmin.', 'warning')
        logger.warning(f"[{current_admin.username}] attempted to revoke admin from superadmin {user.username}.")
    elif not user.is_admin():
        flash(f'{user.username} is not an admin.', 'info')
        logger.info(f"[{current_admin.username}] attempted to revoke admin from {user.username}, who is not an admin.")
    else:
        update_user_by_uuid(user_uuid, role='user')
        flash(f'Admin privileges revoked from {user.username}.', 'success')
        logger.info(f"[{current_admin.username}] revoked admin privileges from {user.username}.")

    return redirect(url_for('admin.view_admins'))

@admin_bp.route('/delete_user/<user_uuid>', methods=['POST'])
@admin_required
def delete_user(user_uuid):
    """
    Delete a user by UUID.
    Only superadmins can delete other superadmins.
    Admins can delete regular users.
    """
    logger.info(f"Admin '{current_user.username}' requested deletion of user {user_uuid}")

    user_to_delete = get_user_by_uuid(user_uuid)
    if not user_to_delete:
        logger.warning(f"Attempted to delete non-existent user: {user_uuid}")
        flash("User not found.", "danger")
        return redirect(url_for('admin.view_users'))

    # Prevent unauthorized deletion of superadmins
    if user_to_delete.is_superadmin() and not current_user.is_superadmin():
        logger.warning(f"Unauthorized deletion attempt: Admin '{current_user.username}' tried to delete superadmin '{user_to_delete.username}'")
        flash("You are not authorized to delete a superadmin.", "danger")
        return redirect(url_for('admin.view_users'))

    # Perform deletion
    delete_user_by_uuid(user_uuid)
    logger.info(f"User '{user_to_delete.username}' (UUID: {user_uuid}) deleted by '{current_user.username}'")
    flash(f"User '{user_to_delete.username}' has been deleted.", "success")

    return redirect(url_for('admin.view_users'))