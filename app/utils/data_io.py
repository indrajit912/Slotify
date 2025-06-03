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

# Define data directories using pathlib for portability and readability
APP_DATA_DIR = Path(Config.APP_DATA_DIR)
EXPORT_DIR = APP_DATA_DIR / "export"
IMPORT_DIR = APP_DATA_DIR / "import"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)
IMPORT_DIR.mkdir(parents=True, exist_ok=True)

def export_model_data(session: SQLAlchemy, model, filename: str, save: bool = False):
    """
    Export all instances of a given model to a JSON file or return the data.

    Args:
        session (SQLAlchemy): The SQLAlchemy session.
        model: The SQLAlchemy model class to export.
        filename (str): Filename to write JSON data to (inside EXPORT_DIR).
        save (bool): If True, save to file. If False, return the data.

    Returns:
        str | list: Summary message if saved, otherwise the list of data dicts.
    """
    data = [obj.to_json() for obj in session.query(model).all()]
    
    if save:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        filepath = EXPORT_DIR / filename
        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return f"{filename} exported with {len(data)} records."
    
    return data


def import_model_data(session, data, from_json_func, key, **kwargs):
    """
    Imports model data from a given dictionary and adds it to the SQLAlchemy session.

    Parameters:
        session (Session): The SQLAlchemy session to use for adding objects.
        data (dict): A dictionary containing JSON lists for various models (like from a full export).
        from_json_func (Callable): A function that converts a JSON dict into a model instance.
        key (str): The key in the `data` dict corresponding to this model's records.
        **kwargs: Additional keyword arguments passed to `from_json_func`.

    Returns:
        str: A summary string indicating how many records were successfully imported.

    Raises:
        KeyError: If the specified key is not found in the `data` dict.

    Example:
        >>> import_model_data(db.session, full_data, Building.from_json, key="buildings")
        'buildings imported with 12 records.'
    """
    if key not in data:
        raise KeyError(f"Key '{key}' not found in provided data.")

    model_data = data[key]
    added = 0
    for item in model_data:
        try:
            obj = from_json_func(item, **kwargs)
            session.add(obj)
            added += 1
        except Exception as e:
            print(f"Skipped due to error: {e}")
    session.commit()
    return f"{key} imported with {added} records."
