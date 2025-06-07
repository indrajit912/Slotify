# manage.py
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
# Standard library imports
import getpass
import os
import logging
from datetime import timedelta, datetime

# Third-party imports
import click
import pytz
from sqlalchemy import inspect
from sqlalchemy.orm import joinedload
from flask.cli import FlaskGroup
from flask.cli import with_appcontext
from flask_migrate import upgrade

# Local application imports
from app import create_app
from config import EmailConfig
from scripts.utils import sha256_hash
from app.extensions import db
from app.models.user import User, ReminderLog
from app.models.building import Building
from app.models.course import Course
from app.services import create_user, create_building
from scripts.utils import utcnow
from scripts.email_message import EmailMessage

IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.utc

cli = FlaskGroup(create_app=create_app)

logger = logging.getLogger(__name__)

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

    Prompts the user for all necessary details: username, names, email, password, contact number, etc.
    First checks for a secret password to authorize the superadmin creation.
    Also prompts to select an existing Building or create a new one.
    """
    if not is_db_initialized():
        click.echo("❌ Database is not initialized.")
        click.echo("➡️  Please run 'flask deploy' first to initialize the database.")
        return

    secret_password = getpass.getpass(prompt="Enter the secret password (Indrajit's password): ")
    stored_hash = os.getenv("SUPERADMIN_CREATION_PASSWORD_HASH")

    if sha256_hash(secret_password) != stored_hash:
        click.echo("❌ Incorrect password. You are not authorized to create a superadmin.")
        return

    click.echo("🔐 Authorization successful. Proceeding to create superadmin.")

    username = click.prompt("Enter username")
    first_name = click.prompt("Enter first name")
    middle_name = click.prompt("Enter middle name", default="", show_default=False)
    last_name = click.prompt("Enter last name", default="", show_default=False)
    email = click.prompt("Enter email address")

    contact_no = click.prompt("Enter contact number", default="", show_default=False)
    room_no = click.prompt("Enter room number", default="", show_default=False)

    password = getpass.getpass(prompt="Enter password: ")
    confirm_password = getpass.getpass(prompt="Confirm password: ")

    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    buildings = Building.query.order_by(Building.name).all()

    if not buildings:
        click.echo("🏢 No buildings found in the system.")
        building_name = click.prompt("Enter the name of the building for the superadmin")
        building_code = click.prompt("Enter the building code (unique short code)")
        building = create_building(name=building_name, code=building_code)
        click.echo(f"✅ Building '{building_name}' created.")
    else:
        click.echo("🏢 Available buildings:")
        for idx, b in enumerate(buildings, start=1):
            click.echo(f"{idx}. {b.name} (Code: {b.code})")
        building_choice = click.prompt("Enter the number of the building", type=int)

        if building_choice < 1 or building_choice > len(buildings):
            click.echo("❌ Invalid choice. Exiting.")
            return

        building = buildings[building_choice - 1]
        click.echo(f"✅ Selected building: {building.name}")

    course = None
    courses = Course.query.order_by(Course.name).all()
    if courses:
        click.echo("🎓 Available courses:")
        for idx, c in enumerate(courses, start=1):
            click.echo(f"{idx}. {c.name}")
        course_choice = click.prompt("Enter the number of the course (or 0 to skip)", type=int, default=0)
        if 1 <= course_choice <= len(courses):
            course = courses[course_choice - 1]
            click.echo(f"✅ Selected course: {course.name}")
        else:
            click.echo("ℹ️ No course selected.")

    try:
        superadmin = create_user(
            username=username,
            first_name=first_name,
            middle_name=middle_name or None,
            last_name=last_name or None,
            email=email,
            password=password,
            role="superadmin",
            contact_no=contact_no or None,
            room_no=room_no or None,
            building_uuid=building.uuid,
            course_uuid=course.uuid if course else None,
        )
        superadmin.email_verified = True
        db.session.commit()
        click.echo(f"🎉 Superadmin created: {superadmin.username} ({superadmin.email})")
    except ValueError as e:
        click.echo(f"❌ Error: {e}")


@cli.command("deploy")
def deploy():
    """Run deployment tasks."""  
    # migrate database to latest revision
    upgrade()


@cli.command("send-reminder-emails")
def send_reminder_emails():
    """Send reminder emails for upcoming bookings, based on user preferences."""
    now_utc = utcnow()
    users = User.query.options(joinedload(User.bookings)).all()
    reminders_sent = 0

    logger.info(f"📬 Running reminder email job at UTC {now_utc.isoformat()} for {len(users)} users.")

    for user in users:
        if not user.is_email_reminder_on():
            continue

        logger.info(f"🔍 Checking bookings for user {user.username} ({user.uuid}).")

        for booking in user.get_upcoming_bookings():
            naive_booking_dt = datetime.combine(booking.date, booking.time_slot.start_hour)
            ist_booking_dt = IST.localize(naive_booking_dt)
            ist_reminder_dt = ist_booking_dt - timedelta(hours=user.email_reminder_hours)
            reminder_dt_utc = ist_reminder_dt.astimezone(UTC)

            if reminder_dt_utc <= now_utc < reminder_dt_utc + timedelta(minutes=60):
                already_sent = ReminderLog.query.filter_by(
                    user_uuid=user.uuid,
                    booking_uuid=booking.uuid
                ).first()

                if already_sent:
                    logger.info(f"🛑 Reminder already sent for booking {booking.uuid} to {user.username}. Skipping.")
                    continue

                try:
                    send_reminder_email(user, booking)
                    db.session.add(ReminderLog(user_uuid=user.uuid, booking_uuid=booking.uuid))
                    logger.info(f"✅ Reminder email sent to {user.username} for booking {booking.uuid}.")
                    reminders_sent += 1
                except Exception as e:
                    logger.exception(f"❌ Failed to send reminder to {user.username} for booking {booking.uuid}: {e}")
            else:
                logger.debug(f"⏳ Booking {booking.uuid} is outside the reminder window.")

    db.session.commit()
    logger.info(f"✅ Reminder email job complete. {reminders_sent} email(s) sent.")
    click.echo(f"✅ {reminders_sent} reminder email(s) sent.")


def send_reminder_email(user, booking):

    naive_booking_dt = datetime.combine(booking.date, booking.time_slot.start_hour)
    ist_booking_dt = IST.localize(naive_booking_dt)
    formatted_time = ist_booking_dt.strftime("%A, %d %B %Y at %I:%M %p")

    subject = f"⏰ Reminder: Your Washing Machine Booking on {booking.date.strftime('%d %b')}"

    html_body = f"""
    <html>
    <body>
        <p>Hi <strong>{user.username}</strong>,</p>
        <p>This is a friendly reminder that you have a washing machine booking scheduled for:</p>
        <ul>
            <li><strong>🗓 Date & Time:</strong> {formatted_time} (IST)</li>
            <li><strong>📍 Location:</strong> {booking.time_slot.machine.name} in {booking.time_slot.machine.building.name}</li>
        </ul>
        <p>Please be on time. If you've already completed your laundry or no longer need the slot, feel free to ignore this reminder.</p>
        <p>Regards,<br><em>Slotify Bot</em></p>
    </body>
    </html>
    """

    email = EmailMessage(
        sender_email_id=EmailConfig.MAIL_USERNAME,
        to=user.reminder_email,
        subject=subject,
        email_html_text=html_body,
        formataddr_text="Slotify Bot"
    )

    logger.debug(f"📧 Sending reminder email to {user.reminder_email} for booking {booking.uuid}.")
    email.send(
        sender_email_password=EmailConfig.MAIL_PASSWORD,
        server_info=EmailConfig.GMAIL_SERVER,
        print_success_status=False
    )

if __name__ == '__main__':
    cli()