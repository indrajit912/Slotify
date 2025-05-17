# app/__init__.py
# Webapp Slotify
# Author: Indrajit Ghosh
# Created On: May 10, 2025

# Standard library imports
import logging

# Third-party imports
from flask import Flask
from flask_wtf.csrf import generate_csrf

# Local application imports
from config import get_config, LOG_FILE
from .extensions import db, migrate, moment, login_manager

def configure_logging(app:Flask):
    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        filename=str(LOG_FILE),
        datefmt='%d-%b-%Y %I:%M:%S %p'
    )

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

     # Initialize extensions
    db.init_app(app)
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
    
    return app