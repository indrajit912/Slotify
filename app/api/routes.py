# app/api/routes.py
# Author: Indrajit Ghosh
# Created On: Jun 01, 2025
#
# Standard library imports
import logging

# Third-party imports
from flask import jsonify, send_file, after_this_request, request
from sqlalchemy import inspect

# Relative imports
from . import api_bp
from app.extensions import db
from app.utils.decorators import token_required
from scripts.export_import import export_all_zipped, import_all_zipped
from app.utils.data_io import IMPORT_DIR

logger = logging.getLogger(__name__)

@api_bp.route('/export', methods=['GET'])
@token_required
def export_data(user_uuid):
    """
    Export all database contents as a ZIP archive.

    This endpoint serializes the entire Slotify database and returns it
    as a downloadable `.zip` file. It is intended for admins to back up data.

    Authentication:
        Requires a valid Bearer token in the Authorization header.

    Request:
        Method: GET
        Headers:
            Authorization: Bearer <token>

    Response (Success - 200 OK):
        Content-Type: application/zip
        Body: ZIP file containing JSON data for all tables.

    Response (Failure - 500 Internal Server Error):
        JSON:
            {
                "error": "Detailed error message"
            }

    Example curl:
        curl -H "Authorization: Bearer <token>" \
             -o slotify_export.zip \
             https://slotify.pythonanywhere.com/api/export

    Notes:
        - The returned file is deleted from the server immediately after the response is sent.
        - Only users with valid tokens can access this endpoint.
    """
    try:
        logger.info(f"[API] Export initiated by user_uuid={user_uuid}")
        zip_path = export_all_zipped(db.session)
        logger.info(f"[API] Export completed successfully for user_uuid={user_uuid}: {zip_path.name}")

        @after_this_request
        def remove_file(response):
            try:
                zip_path.unlink()
                logger.info(f"[API] Temporary export file deleted: {zip_path}")
            except Exception as e:
                logger.warning(f"[API] Failed to delete export file: {zip_path} -> {e}")
            return response

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        logger.exception(f"[API] Export failed for user_uuid={user_uuid}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/import', methods=['POST'])
@token_required
def import_data(user_uuid):
    """
    Import database data from a provided ZIP file.

    This endpoint accepts a `.zip` archive previously exported via the `/export`
    endpoint, and restores the contents into the current database. All relevant
    tables are overwritten.

    Authentication:
        Requires a valid Bearer token in the Authorization header.

    Request:
        Method: POST
        Headers:
            Authorization: Bearer <token>
        Form Data:
            file: ZIP file (application/zip)

    Response (Success - 200 OK):
        JSON:
            {
                "message": "Import successful"
            }

    Response (Client Error - 400 Bad Request):
        JSON:
            {
                "error": "No file part" | "No selected file"
            }

    Response (Server Error - 500 Internal Server Error):
        JSON:
            {
                "error": "Detailed error message"
            }

    Example curl:
        curl -X POST \
             -H "Authorization: Bearer <token>" \
             -F "file=@slotify_export.zip" \
             https://slotify.pythonanywhere.com/api/import

    Notes:
        - The ZIP file must have the expected format and table data.
        - This operation assumes the database schema (tables) already exists.
        - The uploaded file is deleted after import (success or failure).
    """
    # Check if all tables are initialized
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    expected_tables = {
        'user', 'building', 'course', 'washingmachine', 'booking'
        # Add other expected tables here
    }

    if not expected_tables.issubset(set(existing_tables)):
        logger.warning(f"[API] Import aborted: Missing tables in DB. Existing: {existing_tables}")
        return jsonify({'error': 'Database tables are not initialized. Please run migrations first.'}), 500

    # Handle file input
    if 'file' not in request.files:
        logger.warning(f"[API] Import failed (no file part) by user_uuid={user_uuid}")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning(f"[API] Import failed (no selected file) by user_uuid={user_uuid}")
        return jsonify({'error': 'No selected file'}), 400

    temp_path = IMPORT_DIR / file.filename
    file.save(temp_path)
    logger.info(f"[API] Import file received from user_uuid={user_uuid}: {file.filename}")

    try:
        import_all_zipped(db.session, temp_path)
        logger.info(f"[API] Import successful for user_uuid={user_uuid}: {file.filename}")
        return jsonify({'message': 'Import successful'}), 200
    except Exception as e:
        logger.exception(f"[API] Import failed for user_uuid={user_uuid}: {file.filename}")
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_path.exists():
            temp_path.unlink()
            logger.debug(f"[API] Temp file deleted after import: {temp_path}")