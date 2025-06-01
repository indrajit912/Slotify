# app/api/__init__.py
#
# Author: Indrajit Ghosh
# Created On: Jun 01, 2025
#

from flask import Blueprint

api_bp = Blueprint(
    'api', 
    __name__,
    url_prefix='/api'
)

from app.api import routes