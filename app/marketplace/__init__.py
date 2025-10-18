# app/marketplace/__init__.py
# Author: Indrajit Ghosh
# Created On: Oct 18, 2025

from flask import Blueprint
from app.extensions import csrf

marketplace_bp = Blueprint(
    'marketplace',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/marketplace'
)

from app.marketplace import routes

# Disable CSRF only for this blueprint
csrf.exempt(marketplace_bp)