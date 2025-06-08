"""
config.py

Module for configuring the Slotify application.

Author: Indrajit Ghosh
Created on: May 10, 2025

This module provides configuration settings for the Slotify application,
including email configuration, environment settings, and database URIs.
"""
import os
from pathlib import Path
from os.path import join, dirname
from dotenv import load_dotenv
from secrets import token_hex

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

class EmailConfig:
    MAIL_USERNAME = os.environ.get("BOT_GMAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("BOT_APP_PASSWORD")
    GMAIL_SERVER = ['smtp.gmail.com', 587]

class Config:
    FLASK_APP = 'app'
    FLASK_APP_NAME = 'Slotify'
    SUPERADMIN_CREATION_PASSWD_HASH = os.environ.get("SUPERADMIN_CREATION_PASSWD_HASH")

    BASE_DIR = Path(__name__).parent.absolute()
    APP_DATA_DIR = BASE_DIR / "app_data"
    LOG_DIR = BASE_DIR / "logs"
    LOG_FILE = LOG_DIR / f'{FLASK_APP_NAME.lower()}.log'
    SCHEDULER_LOG_FILE = LOG_DIR / "scheduler.log"

    UPLOAD_DIR = BASE_DIR / "app" / "main" / "static" / "uploads" / "machines"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    
    DATABASE_URI = os.environ.get("DATABASE_URI")
    ISI_ROLL_PREFIXES = ['rs_', 'bmat', 'mmat', 'mlis', 'mqms']

    FLASK_ENV = os.environ.get("FLASK_ENV") or 'production'
    if FLASK_ENV in ['dev', 'developement']:
        FLASK_ENV = 'development'
    elif FLASK_ENV in ['prod', 'production', 'pro']:
        FLASK_ENV = 'production'
    else:
        FLASK_ENV = 'development'
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or token_hex(16)

class DevelopmentConfig(Config):
    PORT = os.environ.get("PORT") or 8080
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(Config.BASE_DIR, f'{Config.FLASK_APP_NAME.lower()}.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = Config.DATABASE_URI or \
        'sqlite:///' + os.path.join(Config.BASE_DIR, f'{Config.FLASK_APP_NAME.lower()}.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def get_config():
    """
    Get the appropriate configuration based on the specified environment.
    :return: Config object
    """
    if Config.FLASK_ENV == 'production':
        return ProductionConfig()
    else:
        return DevelopmentConfig()
    
LOG_FILE = Config.LOG_FILE
SCHEDULER_LOG_FILE = Config.SCHEDULER_LOG_FILE

LOG_DIR = Config.LOG_DIR
LOG_DIR.mkdir(exist_ok=True) 