# app/admin/scheduler_routes.py
# Author: Indrajit Ghosh
# Created On: Jun 08, 2025
#
import logging

from flask import flash, redirect, url_for, current_app
from app.utils.decorators import admin_required

from . import admin_bp
from app.scheduler import scheduler, init_scheduler, shutdown_scheduler

logger = logging.getLogger(__name__)

@admin_bp.route("/scheduler/start", methods=["POST"])
@admin_required
def start_scheduler():
    if not scheduler.running:
        init_scheduler(current_app)
        flash("Scheduler started.", "success")
    else:
        flash("Scheduler is already running.", "info")
    return redirect(url_for("admin.home"))

@admin_bp.route("/scheduler/stop", methods=["POST"])
@admin_required
def stop_scheduler():
    if scheduler.running:
        shutdown_scheduler()
        flash("Scheduler stopped.", "warning")
    else:
        flash("Scheduler is not running.", "info")
    return redirect(url_for("admin.home"))
