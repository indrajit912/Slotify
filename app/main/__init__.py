# app/main/__init__.py
#
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#

from flask import Blueprint

main_bp = Blueprint(
    'main', 
    __name__,
    template_folder="templates", 
    static_folder="static",
    static_url_path="/main/static"
)

from app.main import routes