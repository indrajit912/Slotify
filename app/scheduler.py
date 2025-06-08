# app/scheduler.py
# 
# Author: Indrajit Ghosh
# Created On: Jun 08, 2025
#
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def init_scheduler(app):
    """Bind app context and add jobs."""
    from app.services import send_reminder_emails

    @scheduler.scheduled_job("interval", minutes=60)
    def scheduled_reminder_job():
        with app.app_context():
            send_reminder_emails()

    scheduler.start()

def shutdown_scheduler():
    """Shut down the scheduler cleanly."""
    try:
        scheduler.shutdown()
    except:
        pass