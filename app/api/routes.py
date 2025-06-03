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
from app.models.user import CurrentEnrolledStudent, User
from app.models.booking import TimeSlot, Booking
from app.models.building import Building
from app.models.washingmachine import WashingMachine
from app.models.course import Course
from app.utils.decorators import token_required
from scripts.export_import import export_all_json, import_all_json
from app.utils.data_io import IMPORT_DIR

logger = logging.getLogger(__name__)

@api_bp.route('/export', methods=['GET'])
@token_required
def export_data(user_uuid):
    """
    Export all database contents as either a downloadable JSON file or inline JSON response.

    Query Parameters:
        - as_file (bool, optional): If true (default), downloads a .json file.
                                    If false, returns JSON data inline in the response.

    Authentication:
        Requires a valid Bearer token in the Authorization header.

    Request:
        Method: GET
        URL: /api/export
        Headers:
            Authorization: Bearer <token>
        Query Params:
            as_file (optional): "true" (default) or "false"

    Response (Success - 200 OK):
        If as_file=true:
            Content-Type: application/json
            Body: Downloadable JSON file containing all Slotify data.
        If as_file=false:
            Content-Type: application/json
            Body: Inline JSON response.

    Response (Failure - 500 Internal Server Error):
        Content-Type: application/json
        JSON:
            {
                "error": "Detailed error message"
            }

    Example curl:
        curl -H "Authorization: Bearer <token>" \
             -o slotify_export.json \
             https://slotify.pythonanywhere.com/api/export?as_file=true

    Example Postman:
        1. Method: GET
        2. URL: https://slotify.pythonanywhere.com/api/export?as_file=false
        3. Headers:
            Key: Authorization
            Value: Bearer <your_token>
        4. Send the request.
        5. View inline JSON in the response tab,
           or set `as_file=true` to receive a downloadable file.

    Notes:
        - The exported file is deleted from the server immediately after the response is sent.
        - Only authenticated users with valid tokens can access this endpoint.
    """
    try:
        logger.info(f"[API] Export initiated by user_uuid={user_uuid}")

        as_file = request.args.get("as_file", "true").lower() == "true"

        if as_file:
            json_path = export_all_json(db.session, save=True)
            logger.info(f"[API] Exported to file: {json_path}")

            @after_this_request
            def remove_file(response):
                try:
                    json_path.unlink()
                    logger.info(f"[API] Deleted temporary file: {json_path}")
                except Exception as e:
                    logger.warning(f"[API] Failed to delete file: {json_path} -> {e}")
                return response

            return send_file(
                json_path,
                mimetype="application/json",
                as_attachment=True,
                download_name=json_path.name
            )
        else:
            data = export_all_json(db.session, save=False)
            logger.info(f"[API] Exported inline JSON for user_uuid={user_uuid}")
            return jsonify(data)

    except Exception as e:
        logger.exception(f"[API] Export failed for user_uuid={user_uuid}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/import', methods=['POST'])
@token_required
def import_data(user_uuid):
    """
    Import database data from a provided JSON file.
    ...
    (Docstring remains unchanged)
    """
    # Check if all tables are initialized
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()

    expected_tables = {
        'user', 'building', 'course', 'washingmachine', 'booking',
        'timeslot', 'enrolled_student'
    }

    if not expected_tables.issubset(set(existing_tables)):
        logger.warning(f"[API] Import aborted: Missing tables in DB. Existing: {existing_tables}")
        return jsonify({
            'error': (
                "Database tables are not initialized or need to be reset before import. "
                "If you are running this for the first time, please set up the database schema by logging into the server and running:\n\n"
                "    flask db upgrade\n\n"
                "If the database already contains previous data that you want to replace, "
                "you should clear the existing data first to avoid conflicts. This can be done by:\n\n"
                "1. Dropping all tables and recreating them:\n"
                "    flask db downgrade base\n"
                "    flask db upgrade\n\n"
                "2. Or manually truncating tables (if supported) before importing.\n\n"
                "After the database is clean and schema is ready, try the import again."
            )
        }), 500

    # Handle file input
    if 'file' not in request.files:
        logger.warning(f"[API] Import failed (no file part) by user_uuid={user_uuid}")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning(f"[API] Import failed (no selected file) by user_uuid={user_uuid}")
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.lower().endswith('.json'):
        logger.warning(f"[API] Import failed (invalid file type) by user_uuid={user_uuid}: {file.filename}")
        return jsonify({'error': 'Invalid file type. Please upload a JSON file.'}), 400

    temp_path = IMPORT_DIR / file.filename
    file.save(temp_path)
    logger.info(f"[API] Import file received from user_uuid={user_uuid}: {file.filename}")

    # ⛔️ Check for preexisting data before importing
    preexisting_data = {
        'User': db.session.query(User).first(),
        'Building': db.session.query(Building).first(),
        'Course': db.session.query(Course).first(),
        'WashingMachine': db.session.query(WashingMachine).first(),
        'TimeSlot': db.session.query(TimeSlot).first(),
        'Booking': db.session.query(Booking).first(),
        'CurrentEnrolledStudent': db.session.query(CurrentEnrolledStudent).first()
    }

    non_empty = [table for table, entry in preexisting_data.items() if entry]
    if non_empty:
        logger.warning(f"[API] Import aborted: Preexisting data found in {non_empty}")
        return jsonify({
            'error': (
                f"Import failed: The following tables are not empty: {', '.join(non_empty)}. "
                "This API expects a clean database (no existing data). "
                "To reset the database, log into the server and run:\n\n"
                "    flask db downgrade base\n"
                "    flask db upgrade\n\n"
                "Then try importing again."
            )
        }), 500

    try:
        import_all_json(db.session, temp_path)
        logger.info(f"[API] Import successful for user_uuid={user_uuid}: {file.filename}")
        return jsonify({'message': 'Import successful'}), 200
    except Exception as e:
        logger.exception(f"[API] Import failed for user_uuid={user_uuid}: {file.filename}")
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_path.exists():
            temp_path.unlink()
            logger.debug(f"[API] Temp file deleted after import: {temp_path}")
