"""
app/utils/data_io.py

Author: Indrajit Ghosh
Created On: May 28, 2025

This module provides utility functions for exporting and importing data related to SQLAlchemy models
used in the Slotify application. It serializes model instances to JSON and reads them back into the 
database using model-specific deserialization functions.

Directory Structure:
- Data is exported to:   <APP_DATA_DIR>/export/
- Data is imported from: <APP_DATA_DIR>/import/

Usage:
    from app.utils.data_io import export_model_data, import_model_data

Typical use involves calling `export_model_data` to write model data to disk and
`import_model_data` to populate the database from a JSON file using a model's `from_json` method.
"""
import json
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from config import Config

from app.models.building import Building
from app.models.course import Course
from app.models.washingmachine import WashingMachine
from app.models.user import User
from app.models.booking import Booking, TimeSlot

# Define data directories using pathlib for portability and readability
APP_DATA_DIR = Path(Config.APP_DATA_DIR)
EXPORT_DIR = APP_DATA_DIR / "export"
IMPORT_DIR = APP_DATA_DIR / "import"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)
IMPORT_DIR.mkdir(parents=True, exist_ok=True)

def export_model_data(session: SQLAlchemy, model, filename: str):
    """
    Export all instances of a given model to a JSON file.

    Args:
        session (SQLAlchemy): The SQLAlchemy session.
        model: The SQLAlchemy model class to export.
        filename (str): Filename to write JSON data to (inside EXPORT_DIR).

    Returns:
        str: Summary message indicating how many records were exported.
    """
    data = [obj.to_json() for obj in session.query(model).all()]
    filepath = EXPORT_DIR / filename
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return f"{filename} exported with {len(data)} records."


def import_model_data(session, filename, from_json_func, **kwargs):
    """
    Imports model data from a JSON file and adds it to the SQLAlchemy session.

    Parameters:
        session (Session): The SQLAlchemy session to use for adding objects.
        filename (str): The name of the JSON file to import (must be in the import directory).
        from_json_func (Callable): A function that converts a JSON dict into a model instance.
        **kwargs: Additional keyword arguments passed to `from_json_func`.

    Returns:
        str: A summary string indicating how many records were successfully imported.

    Raises:
        FileNotFoundError: If the specified file is not found in the import directory.

    Example:
        >>> from app.models.building import Building
        >>> from app import db
        >>> import_model_data(db.session, "buildings.json", Building.from_json)
        'buildings.json imported with 12 records.'
    """
    path = IMPORT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"{filename} not found in import dir.")

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    added = 0
    for item in data:
        try:
            obj = from_json_func(item, **kwargs)
            session.add(obj)
            added += 1
        except Exception as e:
            print(f"Skipped due to error: {e}")
    session.commit()
    return f"{filename.name} imported with {added} records."
