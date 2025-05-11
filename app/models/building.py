# app/models/building.py
# 
# Author: Indrajit Ghosh
# Created On: May 11, 2025
# 
# Third-party imports
from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
import uuid

# Local application imports
from app.extensions import db
from scripts.utils import utcnow

class Building(db.Model):
    __tablename__ = 'building'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = db.Column(db.String(100), unique=True, nullable=False)

    users = db.relationship("User", back_populates="building")
    machines = db.relationship("WashingMachine", back_populates="building")

    def __repr__(self):
        return f"<Building(name={self.name})>"
