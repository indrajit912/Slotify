# app/admin/__init__.py
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#

from flask import Blueprint

admin_bp = Blueprint(
    'admin', 
    __name__,
    template_folder="templates", 
    static_folder="static",
    url_prefix='/admin'
)

from app.admin import routes, scheduler_routes