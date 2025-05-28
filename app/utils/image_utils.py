"""
app/utils/image_utils.py

Utility functions for handling image uploads in the Slotify application.
Supports saving machine images locally and validating allowed file types.
Designed to be compatible with future migration to cloud storage.

Author: Indrajit Ghosh
Created On: May 28, 2025
"""
from flask import current_app
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed image extension.

    Parameters:
        filename (str): Name of the file to validate.

    Returns:
        bool: True if file has an allowed extension, False otherwise.
    """
    allowed = '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']
    if not allowed:
        logger.warning(f"Disallowed file extension for filename: '{filename}'")
    return allowed


def save_machine_image(file, machine_uuid):
    """
    Save an uploaded image file for a washing machine.

    The file is renamed using the machine UUID to avoid name collisions,
    and saved to the configured UPLOAD_DIR. The function returns a
    relative path that can be stored in the database for future access.

    Parameters:
        file (FileStorage): The uploaded image file (e.g., from Flask-WTF form).
        machine_uuid (str): UUID of the washing machine for generating a unique filename.

    Returns:
        str | None: Relative path to the saved image (e.g., "uploads/machines/uuid_filename.jpg"),
                    or None if file is invalid or not allowed.
    """
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{machine_uuid}_{file.filename}")
        upload_dir = current_app.config['UPLOAD_DIR']

        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / filename
            file.save(file_path)
            logger.info(f"Saved image for machine UUID {machine_uuid} at '{file_path}'")
            return f"uploads/machines/{filename}"
        except Exception as e:
            logger.error(f"Error saving image for machine UUID {machine_uuid}: {e}")
            return None
    else:
        logger.warning(f"File not saved: either no file or disallowed type for machine UUID {machine_uuid}")
        return None
