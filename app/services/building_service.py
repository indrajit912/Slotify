# app/services/building_service.py
#
# Author: Indrajit Ghosh
# Created On: May 11, 2025
# 
import logging

from sqlalchemy.exc import IntegrityError

from app.models.building import Building
from app.extensions import db

logger = logging.getLogger(__name__)

def create_building(name: str):
    """
    Creates and stores a new building in the database.

    Args:
        name (str): The name of the building (e.g., "Hostel 1", "D Quarter").

    Returns:
        Building: The created building object.

    Raises:
        ValueError: If a building with the same name already exists.
    """
    # Check if a building with the same name already exists
    existing_building = Building.query.filter_by(name=name).first()
    if existing_building:
        logger.warning(f"Building with name '{name}' already exists.")
        raise ValueError(f"A building with the name '{name}' already exists.")

    # Create a new building and generate a uuid
    building = Building(name=name)

    # Add the building to the session and commit
    db.session.add(building)
    try:
        db.session.commit()
        logger.info(f"Building '{name}' created successfully with UUID: {building.uuid}.")
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Failed to create building '{name}' due to database error: {e}")
        raise ValueError("Could not create building due to a database error.")

    return building