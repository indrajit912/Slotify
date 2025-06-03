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

def create_building(name: str, code: str):
    """
    Creates and stores a new building in the database.

    Args:
        name (str): The name of the building (e.g., "Hostel 1", "D Quarter").
        code (str): A unique short code for the building (e.g., "HQ1", "DQ").

    Returns:
        Building: The created building object.

    Raises:
        ValueError: If a building with the same name or code already exists.
    """
    # Check if a building with the same name or code already exists
    existing_building = Building.query.filter(
        (Building.name == name) | (Building.code == code)
    ).first()
    if existing_building:
        logger.warning(
            f"Building with name '{name}' or code '{code}' already exists."
        )
        raise ValueError(
            f"A building with the name '{name}' or code '{code}' already exists."
        )

    # Create a new building with uuid generated automatically
    building = Building(name=name, code=code)

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


def get_building_by_uuid(uuid_str: str | None):
    """
    Returns:
        - A single Building object if uuid_str is provided and found.
        - A list of all Building objects if uuid_str is None.
        - None if a specific UUID is given but not found.
    """
    if uuid_str is None:
        buildings = Building.query.all()
        logger.debug(f"Retrieved all buildings: count={len(buildings)}")
        return buildings

    building = Building.query.filter_by(uuid=uuid_str).first()
    if building:
        logger.debug(f"Building found with UUID {uuid_str}: {building.name}")
    else:
        logger.warning(f"No building found with UUID {uuid_str}")

    return building


def update_building_by_uuid(uuid: str, *, name: str = None, code: str = None):
    """
    Updates an existing building identified by UUID.

    Args:
        uuid (str): UUID of the building to update.
        name (str, optional): New name for the building.
        code (str, optional): New unique code for the building.

    Returns:
        Building: The updated building object.

    Raises:
        ValueError: If the building does not exist, or if the new name or code conflicts with another building.
    """
    building = Building.query.filter_by(uuid=uuid).first()
    if not building:
        logger.warning(f"Attempted to update non-existent building UUID: {uuid}")
        raise ValueError("Building not found.")

    logger.info(f"Updating building UUID: {uuid}")

    # Check for name conflict
    if name and name != building.name:
        if Building.query.filter(Building.name == name, Building.uuid != uuid).first():
            logger.warning(f"Building name already taken: {name}")
            raise ValueError(f"A building with the name '{name}' already exists.")
        building.name = name

    # Check for code conflict
    if code and code != building.code:
        if Building.query.filter(Building.code == code, Building.uuid != uuid).first():
            logger.warning(f"Building code already taken: {code}")
            raise ValueError(f"A building with the code '{code}' already exists.")
        building.code = code

    try:
        db.session.commit()
        logger.info(f"Building UUID {uuid} updated successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating building UUID {uuid}: {e}")
        raise ValueError("Could not update building.")

    return building
