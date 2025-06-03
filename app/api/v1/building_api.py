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
from app.services import get_building_by_uuid
from app.utils.decorators import admin_only

logger = logging.getLogger(__name__)

@api_v1.route('/buildings/', methods=['GET'])
@admin_only
def list_buildings(user_data):
    """
    GET /api/v1/buildings/

    List all buildings or a specific building by UUID.
    Requires admin token.

    Query Parameters:
        - building_uuid (optional): UUID of the building to retrieve.

    Response: 200 OK
    - If building_uuid is provided and found:
        {
            "uuid": "...",
            "name": "...",
            "address": "..."
        }
    - If building_uuid is not provided:
        [
            { "uuid": "...", "name": "...", "address": "..." },
            ...
        ]

    Response: 404 Not Found
        {
            "error": "Building not found"
        }
    """
    building_uuid = request.args.get("building_uuid")

    logger.info(f"[API] Admin {user_data['user_uuid']} requested buildings. "
                f"building_uuid={building_uuid}")

    buildings = get_building_by_uuid(building_uuid)

    if building_uuid:
        if not buildings:
            logger.warning(f"[API] No building found with UUID: {building_uuid}")
            return jsonify({'error': 'Building not found'}), 404
        logger.info(f"[API] Building found: {buildings.name} (UUID: {buildings.uuid})")
        return jsonify(buildings.to_json()), 200

    logger.info(f"[API] {len(buildings)} building(s) retrieved.")
    return jsonify([b.to_json() for b in buildings]), 200
