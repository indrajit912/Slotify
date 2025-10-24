# app/auth/routes.py
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#
# Standard library imports
import logging
from datetime import date, datetime

# Third-party imports
from flask import flash, redirect, render_template, url_for, current_app, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_, and_

# Relative imports
from . import auth_bp
from app.forms.auth_forms import UserLoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from app.models.user import User
from app.models.booking import Booking, TimeSlot
from app.models.building import Building
from app.models.course import Course
from app.services import update_user_last_seen, create_user, get_user_by_email, update_user_by_uuid
from app.utils.decorators import logout_required, email_verification_required
from scripts.email_message import EmailMessage
from app.utils.token import generate_registration_token, confirm_registration_token, verify_admin_verification_code
from config import EmailConfig
from app.extensions import db

logger = logging.getLogger(__name__)

@auth_bp.before_request
def update_last_seen():
    if current_user.is_authenticated:
        user_uuid = current_user.uuid
        status = update_user_last_seen(user_uuid)

        if not status:
            logger.error(f"Updating last seen failed for '{current_user.username}'")

# Login view (route)
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = UserLoginForm()
    show_verify_link = False
    email_for_verification = None

    if form.validate_on_submit():
        user_input = form.username_or_email.data
        user = User.query.filter(
            (User.username == user_input) | (User.email == user_input)
        ).first()

        if user:
            if user.check_password(form.passwd.data):
                if user.is_blocked:  # Blocked user check
                    flash("Your account has been blocked. Please contact admins.", "error")
                    logger.warning(f"Blocked user '{user.email}' attempted to log in.")
                elif not user.email_verified:
                    flash("Please verify your email address first.", "warning")
                    show_verify_link = True
                    email_for_verification = user.email
                else:
                    login_user(user)
                    logger.info(f"User '{user.email}' successfully logged in.")
                    flash("Login successful!", 'success')
                    return redirect(url_for('auth.dashboard'))
            else:
                flash("Invalid username or password. Please try again.", "error")
                logger.warning(f"Failed login attempt: incorrect password for '{user_input}'")
        else:
            flash("That user doesn't exist! Try again...", 'error')
            logger.warning(f"Failed login attempt: no such user '{user_input}'")

        # Clear form fields after failure
        form = UserLoginForm(formdata=None)

    return render_template(
        'login.html', form=form,
        show_verify_link=show_verify_link,
        email_for_verification=email_for_verification
    )


@auth_bp.route('/request-email-verification', methods=['POST'])
def request_email_verification():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if not user:
        logger.warning(f"Email verification request failed: no user found with email '{email}'")
        flash("No user found with that email address.", "danger")
        return redirect(url_for('auth.login'))

    if user.email_verified:
        logger.info(f"Email verification request skipped: '{email}' already verified.")
        flash("Your email is already verified. You can log in.", "info")
        return redirect(url_for('auth.login'))

    token = user.generate_email_verification_token()
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    html = render_template(
        'email/email_id_verification_mail.html',
        verification_link=verify_url,
        user=user.first_name
    )

    msg = EmailMessage(
        sender_email_id=EmailConfig.MAIL_USERNAME,
        to=email,
        subject=f"Action Required: Verify your Email Id for {current_app.config['FLASK_APP_NAME']}",
        email_html_text=html,
        formataddr_text=f"{current_app.config['FLASK_APP_NAME']} Bot"
    )

    try:
        msg.send(
            sender_email_password=EmailConfig.MAIL_PASSWORD,
            server_info=EmailConfig.GMAIL_SERVER,
            print_success_status=False
        )
        logger.info(f"Verification email sent to '{email}' with token '{token}'.")
        flash("A verification link has been sent to your email. Please check your Spam folder if you don't see it in your inbox.", "info")
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.exception(f"Failed to send verification email to {email}: {e}")
        flash("Failed to send verification email. Please try again later.", "danger")
        return redirect(url_for('auth.register'))    


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.verify_email_verification_token(token)
    if user:
        user.email_verified = True
        db.session.commit()
        flash("Your email has been verified! You may now log in.", "success")
        return redirect(url_for('auth.login'))
    else:
        flash("Invalid or expired verification link.", "danger")
        return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
@email_verification_required
def dashboard():
    """
    Dashboard view for logged-in users.
    Shows user info, building, washing machines, and recent bookings.
    """
    building = current_user.building
    machines = building.machines if building else []
    today = date.today()

    now = datetime.now()
    today = date.today()
    current_time = now.time()

    # Get all buildings and courses for dropdowns
    all_buildings = Building.query.order_by(Building.name).all()
    all_courses = Course.query.order_by(Course.name).all()

    bookings = (
    Booking.query
    .join(Booking.time_slot)
    .filter(
        Booking.user_id == current_user.id,
        or_(
            Booking.date > today,
            and_(
                Booking.date == today,
                TimeSlot.end_hour >= current_time
            )
        )
    )
    .order_by(Booking.date.asc(), TimeSlot.slot_number.asc())
    .all()
)
    return render_template(
        'dashboard.html',
        user=current_user,
        building=building,
        machines=machines,
        bookings=bookings,
        all_buildings=all_buildings,
        all_courses=all_courses
    )


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully!", 'success')
    logger.info("User logged out successfully.")

    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@logout_required
def register():
    """
    Handle user registration by displaying the form, validating it,
    generating a token, and sending a verification email.
    If the user registers as a guest, send the token only to admins for verification.
    """
    logger.info("Accessed /register route")
    form = RegisterForm()

    # Populate choices with (uuid, name)
    form.building_uuid.choices = [(b.uuid, b.name) for b in Building.query.all()]
    form.course_uuid.choices = [(c.uuid, c.name) for c in Course.query.all()]

    if form.validate_on_submit():
        logger.debug("Register form submitted and validated.")

        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            logger.warning(f"Attempt to register with already registered email: {form.email.data}")
            flash("Email is already registered and verified.", "danger")
            return redirect(url_for('auth.login'))

        form_data = {
            "username": form.username.data,
            "first_name": form.first_name.data,
            "middle_name": form.middle_name.data,
            "last_name": form.last_name.data,
            "email": form.email.data,
            "password": form.password.data,
            "contact_no": form.contact_no.data,
            "room_no": form.room_no.data,
            "building_uuid": form.building_uuid.data,
            "role": form.role_choice.data,
            "course_uuid": form.course_uuid.data if form.role_choice.data == "user" else None,
            "departure_date": form.departure_date.data.isoformat() if form.role_choice.data == "guest" else None,
            "host_name": form.host_name.data if form.role_choice.data == "guest" else None
        }
        building_name = next((name for (uuid, name) in form.building_uuid.choices if uuid == form_data['building_uuid']), None)
        
        token = generate_registration_token(form_data)
        verification_link = url_for('auth.complete_registration', token=token, _external=True)

        if form_data['role'] == 'guest':
            # Send email only to admins, not the guest
            admins = User.query.filter(User.role.in_(['admin', 'superadmin'])).all()
            admin_emails = [admin.email for admin in admins if admin.email_verified]

            if not admin_emails:
                logger.warning("No verified admin emails found to notify guest registration.")
                flash("Registration is temporarily unavailable. Please try again later.", "danger")
                return redirect(url_for('auth.register'))

            guest_info_html = render_template(
                'email/notify_admin_guest_registration.html',
                guest=form_data,
                building_name=building_name,
                verification_link=verification_link,
                config=current_app.config
            )

            admin_msg = EmailMessage(
                sender_email_id=EmailConfig.MAIL_USERNAME,
                to=admin_emails,  # sending to list directly
                subject=f"Guest Registration Request: {form_data['first_name']} {form_data['last_name'] or ''}",
                email_html_text=guest_info_html,
                formataddr_text=f"{current_app.config['FLASK_APP_NAME']} Bot"
            )

            try:
                admin_msg.send(
                    sender_email_password=EmailConfig.MAIL_PASSWORD,
                    server_info=EmailConfig.GMAIL_SERVER,
                    print_success_status=False
                )
                logger.info(f"Admin notification sent to: {admin_emails}")
            except Exception as e:
                logger.exception(f"Failed to notify admins: {e}")
                flash("Failed to send registration request to admins. Please try again later.", "danger")
                return redirect(url_for('auth.register'))

            flash("Your request has been submitted. Admins will verify your details and complete your registration. You will be notified after verification.", "info")
            return redirect(url_for('auth.login'))

        else:
            # Regular user: Send email verification to user
            # Check for Admin Verification Code (AVC)
            avc_code = request.form.get("admin_verification_code", "").strip()

            if avc_code:
                avc_data = verify_admin_verification_code(avc_code)
                if not avc_data:
                    flash("Invalid Admin Verification Code.", "danger")
                    return redirect(url_for('auth.register'))

                # 1️⃣ Check that the admin email belongs to a real admin
                admin = User.query.filter(
                    User.email == avc_data["admin_email"],
                    User.role.in_(["admin", "superadmin"])
                ).first()
                if not admin:
                    flash("The Admin Verification Code was not issued by a valid admin.", "danger")
                    return redirect(url_for('auth.register'))

                # 2️⃣ Check that user email matches
                if avc_data["user_email"].lower() != form.email.data.lower():
                    flash("The Admin Verification Code does not match the entered email address.", "danger")
                    return redirect(url_for('auth.register'))
                
                # Create user directly as email is verified by admin
                try:
                    user = create_user(
                        username=form_data["username"],
                        first_name=form_data["first_name"],
                        middle_name=form_data["middle_name"],
                        last_name=form_data["last_name"],
                        email=form_data["email"],
                        password=form_data["password"],
                        contact_no=form_data["contact_no"],
                        room_no=form_data["room_no"],
                        building_uuid=form_data["building_uuid"],
                        role=form_data["role"],
                        course_uuid=form_data["course_uuid"],
                        email_verified=True,  # <-- key part
                        departure_date=form_data["departure_date"],
                        host_name=form_data["host_name"],
                    )
                    logger.info(f"User created directly via Admin Verification Code: {user.email}")
                    flash("Registration successful! Your email was verified by an admin. You can now log in.", "success")
                    return redirect(url_for('auth.login'))

                except ValueError as e:
                    logger.error(f"Failed to create user via AVC: {e}")
                    flash(str(e), "danger")
                    return redirect(url_for('auth.register'))


            # Regular user: Send email verification to user
            html = render_template(
                'email/verify_email.html',
                verification_link=verification_link,
                user=form_data['first_name']
            )

            msg = EmailMessage(
                sender_email_id=EmailConfig.MAIL_USERNAME,
                to=form_data['email'],
                subject=f"Action Required: Confirm your email for {current_app.config['FLASK_APP_NAME']}",
                email_html_text=html,
                formataddr_text=f"{current_app.config['FLASK_APP_NAME']} Bot"
            )

            try:
                msg.send(
                    sender_email_password=EmailConfig.MAIL_PASSWORD,
                    server_info=EmailConfig.GMAIL_SERVER,
                    print_success_status=False
                )
                logger.info(f"Verification email successfully sent to {form_data['email']}")
            except Exception as e:
                logger.exception(f"Failed to send verification email to {form_data['email']}: {e}")
                flash("Failed to send verification email. Please try again later.", "danger")
                return redirect(url_for('auth.register'))

            flash(
                "A confirmation email has been sent. Please verify to complete registration. "
                "If you don't see it, please check your spam folder. "
                "If you still don’t receive it (even in spam), please contact one of the admins "
                "from your ISI Bangalore email address.",
                "info"
            )


            return redirect(url_for('auth.login'))

    if form.errors:
        logger.debug(f"Form validation errors: {form.errors}")

    return render_template("register.html", form=form)


@auth_bp.route('/complete-registration/<token>')
@logout_required
def complete_registration(token):
    """
    Finalize registration after verifying the token.
    """
    logger.info("Accessed /complete-registration route")
    data = confirm_registration_token(token)
    if not data:
        logger.warning("Invalid or expired registration token encountered.")
        flash("Invalid or expired registration link.", "danger")
        return redirect(url_for('auth.register'))

    if User.query.filter_by(email=data['email']).first():
        logger.info(f"Email already registered: {data['email']}")
        flash("This email is already registered.", "danger")
        return redirect(url_for('auth.login'))

    building = Building.query.filter_by(uuid=data['building_uuid']).first_or_404()

    role = data.get('role', 'user')  # default to user

    if role == 'user':
        course = Course.query.filter_by(uuid=data['course_uuid']).first_or_404()
    else:
        course = None  # guests do not require course

    if role == 'guest':
        if not data.get('contact_no') or not data.get('departure_date') or not data.get('host_name'):
            logger.warning("Guest registration missing required contact_no or departure_date or host_name")
            flash("Incomplete registration data for guest.", "danger")
            return redirect(url_for('auth.register'))

    try:
        departure_date_str = data.get('departure_date')
        departure_date = date.fromisoformat(departure_date_str) if departure_date_str else None
        new_user = create_user(
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            middle_name=data.get('middle_name'),
            last_name=data['last_name'],
            email=data['email'],
            contact_no=data.get('contact_no'),
            room_no=data.get('room_no'),
            building_uuid=building.uuid,
            course_uuid=course.uuid if course else None,
            role=role,
            departure_date=departure_date,
            host_name=data.get('host_name'),
            email_verified=True
        )
        if role == 'user':
            logger.info(f"User created successfully: {new_user.username}")
            flash("Registration complete! You can now log in.", "success")
        elif role == 'guest':
            logger.info(f"Guest created successfully: {new_user.username}")
            flash("Registration complete! The guest can now log in.", "success")
            
            # Send account activation email to the guest
            html = render_template(
                'email/guest_confirmation_email.html',
                guest=new_user.first_name
            )

            msg = EmailMessage(
                sender_email_id=EmailConfig.MAIL_USERNAME,
                to=new_user.email,
                subject=f"Welcome! Your account has been activated on {current_app.config['FLASK_APP_NAME']}",
                email_html_text=html,
                formataddr_text=f"{current_app.config['FLASK_APP_NAME']} Bot"
            )

            try:
                msg.send(
                    sender_email_password=EmailConfig.MAIL_PASSWORD,
                    server_info=EmailConfig.GMAIL_SERVER,
                    print_success_status=False
                )
                logger.info(f"Account activation email successfully sent to {new_user.email}.")
            except Exception as e:
                logger.exception(f"Failed to send account activation email to {new_user.email}: {e}")
                flash("We were unable to send the confirmation email to the guest. Please try again later.", "danger")
                return redirect(url_for('auth.register'))

        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.exception(f"Error during user creation: {e}")
        flash("An error occurred while creating the account. Please try again.", "danger")
        return redirect(url_for('auth.register'))


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
@logout_required
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        user = get_user_by_email(email=email)
        if user:
            reset_passwd_token = user.get_reset_password_token()
            reset_url = url_for('auth.reset_password', token=reset_passwd_token, _external=True)
            html_body = render_template('email/email_reset_password.html', user=user.first_name, reset_url=reset_url)

            current_app.logger.info(f"Password reset requested for user {user.uuid} ({email}). Reset URL: {reset_url}")
            
            # Email
            msg = EmailMessage(
                sender_email_id=EmailConfig.MAIL_USERNAME,
                to=email,
                subject=f"Reset Your {current_app.config['FLASK_APP_NAME']} Password",
                email_html_text=html_body,
                formataddr_text=f"{current_app.config['FLASK_APP_NAME']} Bot"
            )

            try:
                msg.send(
                    sender_email_password=EmailConfig.MAIL_PASSWORD,
                    server_info=EmailConfig.GMAIL_SERVER,
                    print_success_status=False
                )
                logger.info(f"Password Reset email successfully sent to {email}")
            except Exception as e:
                logger.exception(f"Failed to send password reset link email to {email}: {e}")
                flash("Failed to send password reset link email. Please try again later.", "danger")
                return redirect(url_for('auth.login'))

            
            flash('Check your email for instructions to reset your password.', 'info')
        else:
            current_app.logger.warning(f"Password reset requested for non-existent email: {email}")
            flash('If that email is registered, you will receive a reset link shortly.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html', form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
@logout_required
def reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        current_app.logger.warning(f"Invalid or expired password reset token used: {token}")
        flash('The password reset link is invalid or has expired.', 'warning')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        update_user_by_uuid(user_uuid=user.uuid, password=form.password.data)
        current_app.logger.info(f"Password successfully reset for user {user.uuid}")
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', form=form)


@auth_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """
    Allows the currently authenticated user to update their own profile.
    Role updates are explicitly disallowed.
    """
    data = request.form.to_dict()

    # Remove disallowed fields
    data.pop('role', None)

    allowed_fields = {
        'username',
        'email',
        'first_name',
        'middle_name',
        'last_name',
        'password',
        'contact_no',
        'room_no',
        'building_uuid',
        'course_uuid',
        'departure_date',
        'email_reminder_hours',
        'reminder_email'
    }

    # Filter only allowed fields
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    try:
        updated_user = update_user_by_uuid(current_user.uuid, **update_data)
        logger.info(f"User '{updated_user.username}' updated their profile successfully.")
        flash("Profile updated successfully!", 'success')
    except ValueError as ve:
        logger.warning(f"Profile update failed for user '{current_user.username}': {ve}")
        flash(str(ve), 'warning')
    except Exception as e:
        logger.error(f"Unexpected error during profile update for user '{current_user.username}': {e}")
        flash("An unexpected error occurred. Please try again later.", 'danger')

    return redirect(url_for("auth.dashboard"))
