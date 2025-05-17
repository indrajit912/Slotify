# app/models/course.py
# 
# Author: Indrajit Ghosh
# Created On: May 17, 2025
# 
import uuid

# Local application imports
from app.extensions import db

class Course(db.Model):
    __tablename__ = 'course'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)

    # Identifiers
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., "PhD-MATH", "MStat"
    name = db.Column(db.String(100), nullable=False)              # Full name of the course
    short_name = db.Column(db.String(50), nullable=True)          # Optional short name, e.g., "PhD Math"

    # Classification
    level = db.Column(db.String(20), nullable=False)              # e.g., "UG", "PG", "PhD"
    department = db.Column(db.String(100), nullable=False)        # e.g., "Mathematics", "Statistics"

    # Duration and timing
    duration_years = db.Column(db.Integer, nullable=True)         # e.g., 2, 5

    # Administrative
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)

    # Relationships
    users = db.relationship('User', back_populates='course', lazy=True)

    def __repr__(self):
        return f"<Course {self.code}: {self.name}>"