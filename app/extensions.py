# app/extensions.py
#
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_moment import Moment
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
moment = Moment()
login_manager = LoginManager()
