# app/api/__init__.py
#
# Author: Indrajit Ghosh
# Created On: Jun 03, 2025
#

from flask import Blueprint

api_v1 = Blueprint(
    'api_v1', 
    __name__,
    url_prefix='/api/v1'
)

from app.api.v1 import (
    auth_api,
    db_management_api, 
    building_api,
    user_api
)