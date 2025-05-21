# app/services/course_service.py
#
# Author: Indrajit Ghosh
# Created On: May 17, 2025
# 
import logging

from sqlalchemy.exc import IntegrityError

from app.models.course import Course
from app.extensions import db

logger = logging.getLogger(__name__)

def create_new_course(
    *, 
    code, 
    name, 
    level, 
    department, 
    short_name=None, 
    duration_years=None, 
    description=None, 
    is_active=True
):
    """
    Creates and stores a new course.

    Keyword-only arguments:
        code (str): Unique course code.
        name (str): Full course name.
        level (str): Course level, e.g., "UG", "PG", "PhD".
        department (str): Department offering the course.
        short_name (str, optional): Optional short name.
        duration_years (int, optional): Duration in years.
        description (str, optional): Description.
        is_active (bool, optional): Active status (defaults to True).

    Returns:
        Course: The created course object.

    Raises:
        ValueError: If course code already exists or other DB error.
    """
    existing = Course.query.filter_by(code=code).first()
    if existing:
        logger.warning(f"Course code already exists: {code}")
        raise ValueError("Course code already exists.")

    course = Course(
        code=code,
        name=name,
        level=level,
        department=department,
        short_name=short_name,
        duration_years=duration_years,
        description=description,
        is_active=is_active,
    )

    db.session.add(course)
    try:
        db.session.commit()
        logger.info(f"Course created successfully: {code} ({name})")
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Failed to create course {code} due to DB error: {e}")
        raise ValueError("Could not create course due to a database error.")

    return course


def get_course(course_uuid):
    course = Course.query.filter_by(uuid=course_uuid).first()
    if not course:
        logger.warning(f"Course not found with UUID: {course_uuid}")
        raise ValueError("Course not found.")
    return course


def update_course(course_uuid, **kwargs):
    course = Course.query.filter_by(uuid=course_uuid).first()
    if not course:
        logger.warning(f"Attempted to update non-existent course UUID: {course_uuid}")
        raise ValueError("Course not found.")

    logger.info(f"Updating course {course.code} (UUID: {course_uuid})")

    if 'code' in kwargs:
        new_code = kwargs['code']
        if new_code != course.code and Course.query.filter_by(code=new_code).first():
            logger.warning(f"Course code already taken: {new_code}")
            raise ValueError("Course code already taken.")
        course.code = new_code

    attrs = ['name', 'short_name', 'level', 'department', 'duration_years', 'description', 'is_active']
    for attr in attrs:
        if attr in kwargs:
            setattr(course, attr, kwargs[attr])

    try:
        db.session.commit()
        logger.info(f"Course {course.code} (UUID: {course_uuid}) updated successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating course UUID {course_uuid}: {e}")
        raise ValueError("Could not update course.")

    return course


def delete_course(course_uuid):
    course = Course.query.filter_by(uuid=course_uuid).first()
    if not course:
        logger.warning(f"Attempted to delete non-existent course UUID: {course_uuid}")
        raise ValueError("Course not found.")

    try:
        db.session.delete(course)
        db.session.commit()
        logger.info(f"Course {course.code} (UUID: {course_uuid}) deleted successfully.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting course UUID {course_uuid}: {e}")
        raise ValueError("Could not delete course.")
