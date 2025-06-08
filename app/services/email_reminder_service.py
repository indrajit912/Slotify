# app/services/email_reminder_service.py
#
# Author: Indrajit Ghosh
# Created On: Jun 08, 2025
#
import logging
from datetime import timedelta, datetime

import pytz
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.user import User, ReminderLog
from scripts.email_message import EmailMessage
from config import EmailConfig
from scripts.utils import utcnow

logger = logging.getLogger(__name__)


IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.utc

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