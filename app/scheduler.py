# app/scheduler.py
# 
# Author: Indrajit Ghosh
# Created On: Jun 08, 2025
#
# NOTE: This feature is not working in pythonanywhere free of cost.
# If you wanna use this then add these following inside create_app().
# Also the function send_reminder_emails() is not wrapped in app_context.
"""    
    # Initialize scheduler
    from app.scheduler import init_scheduler
    init_scheduler(app)
"""
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
    scheduler.shutdown()