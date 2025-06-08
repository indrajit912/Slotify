# app/admin/routes.py
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
# Standard library imports
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Third-party imports
from flask import flash, redirect, render_template, request, url_for, current_app, jsonify, abort
from flask_login import current_user
from sqlalchemy import desc

# Local application imports
from . import admin_bp
from app.models.user import User, CurrentEnrolledStudent
from app.models.washingmachine import WashingMachine
from app.models.building import Building
from app.models.course import Course
from app.utils.decorators import admin_required
from app.utils.student_parser import parse_enrolled_students
from app.utils.image_utils import save_machine_image
from app.utils.token import generate_api_token
from scripts.utils import utcnow
from app.services import (
    create_washing_machine, 
    create_building,
    search_users,
    update_user_by_uuid, 
    delete_user_by_uuid, 
    get_user_by_uuid, 
    update_course, 
    create_new_course,
    update_building_by_uuid,
    delete_enrolled_students,
    update_washing_machine,
    create_new_enrolled_student,
    update_enrolled_student
)

logger = logging.getLogger(__name__)

@admin_bp.route('/')
@admin_required
def home():
    logger.info(f"Admin dashboard visited by the admin '{current_user.first_name} <{current_user.username}>'.")
    return render_template('admin.html', admin=current_user)


@admin_bp.route('/admins')
@admin_required
def view_admins():
    """View all users with role admin or superadmin."""
    admins = User.query.filter(User.role.in_(['admin', 'superadmin'])).order_by(desc(User.date_joined)).all()
    logger.info(f"Admin '{current_user.first_name} <{current_user.username}>' viewed all admins.")
    return render_template('view_admins.html', admins=admins)


@admin_bp.route('/users')
@admin_required
def view_users():
    """View all non-admin users."""
    users = User.query.filter(User.role == 'user').order_by(desc(User.date_joined)).all()
    buildings = Building.query.order_by(Building.name).all()
    logger.info(f"Admin '{current_user.first_name} <{current_user.username}>' viewed all users.")
    return render_template('view_users.html', users=users, buildings=buildings)

@admin_bp.route('/guests')
@admin_required
def view_guests():
    """View all Guests."""
    users = User.query.filter(User.role == 'guest').order_by(desc(User.date_joined)).all()
    buildings = Building.query.order_by(Building.name).all()
    logger.info(f"Admin '{current_user.first_name} <{current_user.username}>' viewed all guests.")
    return render_template('view_guests.html', users=users, buildings=buildings)


@admin_bp.route('/machines')
@admin_required
def view_machines():
    """View all washing machines."""
    current_year = datetime.now().year
    current_month_num = datetime.now().month
    all_buildings = Building.query.all()
    machines = WashingMachine.query.order_by(desc(WashingMachine.created_at)).all()
    logger.info(f"Admin '{current_user.first_name} <{current_user.username}>' viewed all washing machines.")
    return render_template(
        'view_machines.html', 
        machines=machines, 
        current_year=current_year, 
        current_month_num=current_month_num,
        all_buildings=all_buildings
    )

@admin_bp.route('/buildings')
@admin_required
def view_buildings():
    """View all buildings."""
    buildings = Building.query.order_by(Building.name).all()
    logger.info(f"Admin '{current_user.first_name} <{current_user.username}>' viewed all buildings.")
    return render_template('view_buildings.html', buildings=buildings)

@admin_bp.route('/courses')
@admin_required
def view_courses():
    """View all courses."""
    courses = Course.query.order_by(Course.name).all()
    logger.info(f"Admin '{current_user.first_name} <{current_user.username}>' viewed all courses.")
    return render_template('view_courses.html', courses=courses)

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
        return redirect(url_for('admin.view_buildings'))
    
@admin_bp.route('/courses/create', methods=['POST'])
@admin_required
def create_course_route():
    try:
        is_active = 'is_active' in request.form  # Checkbox handling

        create_new_course(
            code=request.form.get('code'),
            name=request.form.get('name'),
            short_name=request.form.get('short_name') or None,
            level=request.form.get('level'),
            department=request.form.get('department'),
            duration_years=request.form.get('duration_years') or None,
            description=request.form.get('description') or None,
            is_active=is_active,
        )

        flash("Course created successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        logger.error(f"Unexpected error creating course: {e}")
        flash("An unexpected error occurred while creating the course.", "danger")

    return redirect(url_for('admin.view_courses'))
    
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
    

@admin_bp.route('/edit_machine/<string:machine_uuid>', methods=['POST'])
@admin_required
def edit_machine(machine_uuid):
    try:
        name = request.form.get('name')
        code = request.form.get('code')
        status = request.form.get('status')
        image_url = request.form.get('image_url')
        image_file = request.files.get('image_file')


        update_fields = {}
        if name:
            update_fields['name'] = name
        if code:
            update_fields['code'] = code
        if status:
            update_fields['status'] = status

        # If image file uploaded, save it and update image_path
        if image_file and image_file.filename:
            image_path = save_machine_image(image_file, machine_uuid)
            if image_path:
                update_fields['image_path'] = image_path
        # Else if image_url provided, update image_url field
        elif image_url:
            update_fields['image_url'] = image_url

        update_washing_machine(machine_uuid, **update_fields)
        flash(f"Washing machine '{name}' updated successfully.", "success")
    except Exception as e:
        flash(str(e), "danger")

    return redirect(request.referrer or url_for('admin.machines_list'))
    

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

@admin_bp.route('/update_user/<user_uuid>', methods=['POST'])
@admin_required
def update_user(user_uuid):
    """
    Update user details via admin panel.
    Only accessible to admins.
    """
    logger.info(f"Admin '{current_user.username}' requested update for user {user_uuid}")

    user = get_user_by_uuid(user_uuid)
    if not user:
        logger.warning(f"Attempted to update non-existent user: {user_uuid}")
        flash("User not found.", "danger")
        return redirect(url_for('admin.view_users'))

    form_data = request.form.to_dict()

    try:
        update_user_by_uuid(user_uuid, **form_data)
        logger.info(f"User '{user.username}' (UUID: {user_uuid}) updated by '{current_user.username}'")
        flash(f"User '{user.username}' has been updated successfully.", "success")
    except ValueError as ve:
        logger.warning(f"Update failed for user '{user.username}' (UUID: {user_uuid}) — {ve}")
        flash(str(ve), "danger")
    except Exception as e:
        logger.exception(f"Unexpected error while updating user {user_uuid}")
        flash("An unexpected error occurred while updating the user.", "danger")

    return redirect(url_for('admin.view_users'))


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

@admin_bp.route('/update-course/<string:course_uuid>', methods=['POST'])
@admin_required
def update_course_route(course_uuid):
    """Admin route to update a course."""
    try:
        kwargs = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'short_name': request.form.get('short_name'),
            'level': request.form.get('level'),
            'department': request.form.get('department'),
            'duration_years': int(request.form.get('duration_years')) if request.form.get('duration_years') else None,
            'description': request.form.get('description'),
            'is_active': 'is_active' in request.form
        }

        # Remove None values for fields not submitted
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        updated = update_course(course_uuid, **kwargs)
        flash(f"Course '{updated.code}' updated successfully.", "success")
    except ValueError as ve:
        flash(str(ve), "danger")
    except Exception as e:
        logger.exception(f"Unexpected error in updating course UUID: {course_uuid}")
        flash("An unexpected error occurred while updating the course.", "danger")

    return redirect(url_for('admin.view_courses'))

@admin_bp.route('/buildings/<uuid:building_uuid>/update', methods=['POST'])
def update_building_route(building_uuid):
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()

    if not name or not code:
        flash("Both name and code are required.", "danger")
        return redirect(url_for('admin.view_buildings'))

    try:
        update_building_by_uuid(str(building_uuid), name=name, code=code)
        flash("Building updated successfully.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for('admin.view_buildings'))


@admin_bp.route('/current-enrolled-students', methods=['GET'])
@admin_required
def current_enrolled_students():
    """
    Render page with form to paste students and preview the current enrolled students.
    """
    students = CurrentEnrolledStudent.query.order_by(CurrentEnrolledStudent.added_at.desc()).all()
    return render_template('current_enrolled_students.html', students=students)


@admin_bp.route('/add-students', methods=['POST'])
@admin_required
def add_students():
    raw_text = request.form.get('student_data', '').strip()
    if not raw_text:
        flash('No student data provided.', 'warning')
        return redirect(url_for('admin.current_enrolled_students'))

    students = parse_enrolled_students(raw_text)

    added_count = 0
    skipped_count = 0

    for fullname, email in students:
        try:
            create_new_enrolled_student(fullname=fullname, email=email)
            added_count += 1
        except ValueError as e:
            # Most likely: "Email already exists"
            skipped_count += 1
            continue
        except Exception as e:
            # For unexpected errors
            flash(f"Unexpected error while adding student {fullname}: {e}", "danger")
            continue

    flash(f"Added {added_count} new students. Skipped {skipped_count} existing.", 'success')
    return redirect(url_for('admin.current_enrolled_students'))


@admin_bp.route('/update-student', methods=['POST'])
@admin_required
def update_student():
    student_uuid = request.form.get('uuid')
    fullname = request.form.get('fullname', '').strip()
    email = request.form.get('email', '').strip()

    if not student_uuid:
        flash("Student UUID is required for update.", "danger")
        return redirect(url_for('admin.current_enrolled_students'))

    try:
        updated_student = update_enrolled_student(
            uuid=student_uuid,
            fullname=fullname if fullname else None,
            email=email if email else None
        )
        flash(f"Updated student: {updated_student.fullname}", "success")
    except ValueError as ve:
        flash(str(ve), "warning")
    except Exception as e:
        flash(f"Unexpected error: {e}", "danger")

    return redirect(url_for('admin.current_enrolled_students'))


@admin_bp.route('/get-student-by-email')
@admin_required
def get_student_by_email():
    email = request.args.get('email', '').strip()
    if not email:
        return {"error": "Email required"}, 400

    student = CurrentEnrolledStudent.query.filter_by(email=email).first()
    if not student:
        return {"error": "Student not found"}, 404

    return {
        "uuid": student.uuid,
        "fullname": student.fullname,
        "email": student.email
    }


@admin_bp.route('/delete_enrolled_students', methods=['POST'])
@admin_required
def delete_enrolled_students_route():
    student_uuid = request.form.get('student_uuid')

    success = delete_enrolled_students(student_uuid)
    if success:
        if student_uuid:
            flash("Student has been deleted successfully.", "success")
            logger.info(f"Admin {current_user.first_name} (Username: {current_user.username}) deleted student with UUID {student_uuid}.")
        else:
            flash("All enrolled students have been deleted successfully.", "success")
            logger.info(f"Admin {current_user.first_name} (Username: {current_user.username}) deleted all enrolled students.")
    else:
        if student_uuid:
            flash("Failed to delete the student. Please try again.", "danger")
            logger.error(f"Admin {current_user.first_name} (Username: {current_user.username}) failed to delete student with UUID {student_uuid}.")
        else:
            flash("Failed to delete enrolled students. Please try again.", "danger")
            logger.error(f"Admin {current_user.first_name} (Username: {current_user.username}) failed to delete enrolled students.")

    return redirect(url_for('admin.current_enrolled_students'))


@admin_bp.route('/users/search')
def search_users_page():
    users = search_users(
        username=request.args.get('username'),
        fullname=request.args.get('fullname'),
        email=request.args.get('email'),
        contact_no=request.args.get('contact_no'),
        role=request.args.get('role'),
        building_uuid=request.args.get('building_uuid'),
        course_uuid=request.args.get('course_uuid')
    )
    return render_template('search_users.html', users=users)

@admin_bp.route('/logs/view/<log_type>')
@admin_required
def view_logs(log_type):
    log_path = _get_log_path(log_type)

    try:
        log_content = log_path.read_text()
        file_size = log_path.stat().st_size  # Size in bytes
        last_modified = datetime.fromtimestamp(log_path.stat().st_mtime)
        num_lines = log_content.count('\n')

        return render_template(
            'view_logs.html',
            log_content=log_content,
            log_type=log_type,
            file_size=file_size,
            last_modified=last_modified,
            num_lines=num_lines
        )
    except Exception as e:
        current_app.logger.error(f"Failed to read {log_type} log file: {e}")
        abort(500, description=f"Could not read the {log_type} log file.")


@admin_bp.route('/logs/clear/<log_type>', methods=['POST'])
@admin_required
def clear_logs(log_type):
    log_path = _get_log_path(log_type)

    try:
        log_path.write_text("")
        flash(f"{log_type.capitalize()} logs have been cleared.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to clear {log_type} log file: {e}")
        flash(f"Failed to clear {log_type} logs.", "danger")

    return redirect(url_for('admin.view_logs', log_type=log_type))


def _get_log_path(log_type: str):
    if log_type == 'app':
        return current_app.config['LOG_FILE']
    elif log_type == 'scheduler':
        return current_app.config['SCHEDULER_LOG_FILE']
    else:
        abort(400, description="Invalid log type requested.")

@admin_bp.route('/tokens/<user_uuid>', methods=['GET'])
@admin_required
def token_page(user_uuid):
    logger.info(f"[Admin] Token page accessed for user_uuid={user_uuid}")
    user = User.query.filter_by(uuid=user_uuid).first_or_404()
    default_days = 15
    return render_template('token_page.html', user=user, default_days=default_days)


@admin_bp.route('/tokens/<user_uuid>/generate', methods=['POST'])
@admin_required
def generate_token(user_uuid):
    logger.info(f"[Admin] Token generation requested for user_uuid={user_uuid}")
    user = User.query.filter_by(uuid=user_uuid).first_or_404()

    days = request.json.get('days', 15)
    try:
        days = int(days)
        if days <= 0:
            raise ValueError("Days must be positive")
    except Exception as e:
        logger.warning(f"[Admin] Invalid days parameter for user_uuid={user_uuid}: {days} - {e}")
        return jsonify({'error': 'Invalid days parameter'}), 400

    try:
        token = generate_api_token(user_uuid, expires_in_days=days)
        expiry_date = (utcnow() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M UTC')
        logger.info(f"[Admin] Token generated for user_uuid={user_uuid}, expires_on={expiry_date}")
        return jsonify({
            'token': token,
            'expires_on': expiry_date,
            'message': f"Token expires on {expiry_date}. Please copy and keep it in a secure place. This token will not be shown again."
        })
    except Exception as e:
        logger.exception(f"[Admin] Failed to generate token for user_uuid={user_uuid}: {e}")
        return jsonify({'error': 'Failed to generate token'}), 500
