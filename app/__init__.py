# app/__init__.py
# Webapp Slotify
# Author: Indrajit Ghosh
# Created On: May 10, 2025

# Standard library imports
import logging

# Third-party imports
from flask import Flask, render_template
from flask_wtf.csrf import generate_csrf
from logging.handlers import RotatingFileHandler

# Local application imports
from config import get_config, LOG_FILE, SCHEDULER_LOG_FILE
from .extensions import db, migrate, moment, login_manager, csrf

def configure_logging(app:Flask):
    # --- Main application logger ---
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        filename=str(LOG_FILE),
        datefmt='%d-%b-%Y %I:%M:%S %p'
    )

    # --- APScheduler logger ---
    aplogger = logging.getLogger('apscheduler')
    aplogger.propagate = False
    aphandler = logging.FileHandler(str(SCHEDULER_LOG_FILE))
    aphandler = RotatingFileHandler(
        filename=str(SCHEDULER_LOG_FILE),
        maxBytes=1_000_000,  # 1 MB
        backupCount=5        # Keep last 5 log files
    )
    aphandler.setFormatter(logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        datefmt='%d-%b-%Y %I:%M:%S %p'
    ))
    aplogger.addHandler(aphandler)

    if app.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
        # Fix werkzeug handler in debug mode
        logging.getLogger('werkzeug').handlers = []


def create_app(config_class=get_config()):
    """
    Creates an app with specific config class
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    configure_logging(app)

    # Add cli commands
    from manage import create_superadmin, deploy
    app.cli.add_command(deploy)
    app.cli.add_command(create_superadmin)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    moment.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.main import main_bp
    app.register_blueprint(main_bp)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.admin import admin_bp
    app.register_blueprint(admin_bp)

    from app.api import api_v1
    csrf.exempt(api_v1)
    app.register_blueprint(api_v1)

    # Define the user loader function
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User  # Import your User model
        return User.query.get(int(user_id))

    # Inject csrf_token globally for templates
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

    @app.route('/test/')
    def test():
        return '<h1>Testing page of Slotify Flask Application!</h1>'
    
    @app.errorhandler(Exception)
    def unhandled_exception(e):
        app.logger.exception("Unhandled exception: %s", e)
        return render_template("errors/500.html"), 500

    
    return app