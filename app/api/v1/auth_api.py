# app/api/routes.py
# Author: Indrajit Ghosh
# Created On: Jun 03, 2025
#
# Standard library imports
import logging

# Third-party imports
from flask import jsonify, request

# Relative imports
from . import api_v1
from app.services import get_user_by_uuid, create_user
from app.utils.decorators import admin_only

logger = logging.getLogger(__name__)


@api_v1.route('/auth/register', methods=['POST'])
@admin_only
def register(user_data):
    """
    Register a new user.

    Creates a new user account with the provided information.
    Only accessible to authenticated admins.

    Request:
        Method: POST
        URL: /api/v1/auth/register
        Headers:
            Authorization: Bearer <admin_token>
        JSON Body:
            {
                "building_uuid": "9311cd692a3b4525be87252144cea33d",
                "contact_no": "",
                "course_uuid": "",
                "email": "hello@isibang.ac.in",
                "email_verified": true,
                "first_name": "Rockstar",
                "last_name": "",
                "middle_name": "",
                "password": "test@123",
                "room_no": "RG 6",
                "username": "rocking",
                "role": "guest"
            }

    Response (Success - 201 Created):
        Content-Type: application/json
        {
            "message": "User registered successfully",
            "user": {
                ...user fields...
            }
        }

    Response (Failure - 400 Bad Request):
        {
            "error": "Invalid JSON"
        }

    Response (Failure - 403 Forbidden):
        {
            "error": "Admin not found"
        }

    Response (Failure - 500 Internal Server Error):
        {
            "error": "Detailed error message"
        }

    Notes:
        - Only admins (including superadmins) can register new users.
        - The `email_verified` flag is `false` by default.
        - For guests, `departure_date` and `host_name` should be included.
    """
    logger.info(f"[API] Register called by user_uuid={user_data.get('user_uuid')}")

    admin = get_user_by_uuid(user_data['user_uuid'])
    if not admin:
        logger.warning("[API] Admin user not found or unauthorized access attempt")
        return jsonify({'error': 'Only admins are authorized to perform this action'}), 403

    data = request.get_json()
    if not data:
        logger.warning("[API] Invalid JSON in request")
        return jsonify({'error': 'Invalid JSON'}), 400
    
    # 🛡️ Check for superadmin role in request
    if data.get('role') == 'superadmin' and not admin.is_superadmin():
        logger.warning("[API] Non-superadmin attempted to create a superadmin user")
        return jsonify({'error': 'Only superadmins can create another superadmin'}), 403

    try:
        new_user = create_user(**data)
        logger.info(f"[API] New user created with uuid={new_user.uuid} by admin_uuid={admin.uuid}")
        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_json()
        }), 201
    except Exception as e:
        logger.exception("[API] User registration failed")
        return jsonify({'error': str(e)}), 500