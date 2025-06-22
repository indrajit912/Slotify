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
from app.services import get_user_by_uuid, update_user_by_uuid, search_users
from app.utils.decorators import admin_only

logger = logging.getLogger(__name__)

@api_v1.route('/users/', methods=['GET'])
@api_v1.route('/users/<uuid_str>', methods=['GET'])
@admin_only
def list_users(user_data, uuid_str=None):
    """
    GET /api/v1/users/ or /api/v1/users/<uuid>

    List all users or retrieve a specific user by UUID.
    Requires a valid admin token.

    Path Parameters (optional):
        uuid_str (str): UUID of the user to retrieve.

    Response (200 OK):
        If UUID is provided and user exists:
            {
                "uuid": "...",
                "username": "...",
                ...
            }
        If no UUID is provided:
            [
                {
                    "uuid": "...",
                    "username": "...",
                    ...
                },
                ...
            ]

    Response (404 Not Found):
        {
            "error": "User not found"
        }

    Response (403 Forbidden):
        {
            "error": "Unauthorized access"
        }

    Example:
        curl -H "Authorization: Bearer <admin_token>" https://yourdomain/api/v1/users/
        curl -H "Authorization: Bearer <admin_token>" https://yourdomain/api/v1/users/123e4567...
    """
    if uuid_str:
        logger.info(f"[API] User lookup initiated for UUID: {uuid_str}")
        user = get_user_by_uuid(uuid_str)
        if user:
            return jsonify(user.to_json()), 200
        else:
            logger.warning(f"[API] No user found with UUID: {uuid_str}")
            return jsonify({'error': 'User not found'}), 404

    logger.info(f"[API] Fetching all users by admin UUID: {user_data['user_uuid']}")
    users = get_user_by_uuid()  # returns list if uuid_str is None
    return jsonify([u.to_json() for u in users]), 200


@api_v1.route('/users/<user_uuid>', methods=['PUT'])
@admin_only
def update_user(user_data, user_uuid):
    """
    Update an existing user's information by UUID.

    Only accessible to admins.

    Request:
        Method: PUT
        URL: /api/v1/users/<user_uuid>
        Headers:
            Authorization: Bearer <admin_token>
        Body (JSON): Any subset of user fields to update, e.g.,
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "role": "admin",
                "password": "new_password",
                "building_uuid": "...",
                ...
            }

    Response:
        200 OK
        {
            "message": "User updated successfully",
            "user": { ... updated user JSON ... }
        }

        400 Bad Request (Invalid data or username/email conflicts)
        404 Not Found (User UUID not found)
        403 Forbidden (Not admin)
    """
    data = request.get_json()
    if not data:
        logger.warning(f"Empty JSON payload in update request for user UUID: {user_uuid}")
        return jsonify({"error": "Invalid JSON payload"}), 400
    
    # Identify the user making this API call
    caller = get_user_by_uuid(user_data['user_uuid'])

    # Check for superadmin role in request
    if data.get('role') == 'superadmin' and not caller.is_superadmin():
        logger.warning("[API] Non-superadmin attempted to create a superadmin user")
        return jsonify({'error': 'Only superadmins can make another superadmin'}), 403

    try:
        user = update_user_by_uuid(user_uuid, acting_user=caller, **data)
        logger.info(f"User UUID {user_uuid} updated by admin {user_data['user_uuid']}")
        return jsonify({
            "message": "User updated successfully",
            "user": user.to_json()
        }), 200

    except ValueError as ve:
        logger.warning(f"Update failed for user UUID {user_uuid}: {ve}")
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        logger.error(f"Unexpected error updating user UUID {user_uuid}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@api_v1.route('/users/search', methods=['GET'])
@admin_only
def search_user_api(user_data):
    """
    Search users by various fields.

    Only accessible to admins.

    Request:
        Method: GET
        URL: /api/v1/users/search
        Query Parameters (all optional):
            uuid
            username
            first_name
            middle_name
            last_name
            fullname
            email
            role
            contact_no
            building_uuid
            course_uuid

    Response:
        200 OK
        [
            { user1 JSON }, { user2 JSON }, ...
        ]

        400 Bad Request (if query param validation fails)
        403 Forbidden (if not admin)
    """
    try:
        # Extract query parameters (None if missing)
        params = {key: request.args.get(key) for key in [
            'uuid', 'username', 'first_name', 'middle_name', 'last_name', 'fullname',
            'email', 'role', 'contact_no', 'building_uuid', 'course_uuid'
        ]}

        # Clean empty strings to None
        for k, v in params.items():
            if v == "":
                params[k] = None

        users = search_users(**params)

        logger.info(f"Admin {user_data['user_uuid']} searched users with params: {params}. Found {len(users)} results.")

        return jsonify([u.to_json() for u in users]), 200

    except Exception as e:
        logger.error(f"Error during user search: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
