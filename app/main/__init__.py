# app/main/__init__.py
#
# Author: Indrajit Ghosh
# Created On: May 10, 2025
# Modified On: May 27, 2025
#

from flask import Blueprint, render_template

main_bp = Blueprint(
    'main', 
    __name__,
    template_folder="templates", 
    static_folder="static",
    static_url_path="/main/static"
)

from app.main import routes, api_docs_route

@main_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@main_bp.app_errorhandler(500)
def internal_server_error(error):
    return render_template('errors/500.html'), 500

@main_bp.app_errorhandler(401)
def unauthorized_error(error):
    return render_template('errors/401.html'), 401

@main_bp.app_errorhandler(422)
def unprocessable_entity_error(error):
    return render_template('errors/422.html'), 422
