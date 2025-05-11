# app/models/washingmachine.py
# 
# Author: Indrajit Ghosh
# Created On: May 10, 2025
# 
import uuid
from app.extensions import db
from scripts.utils import utcnow

class WashingMachine(db.Model):
    __tablename__ = 'washingmachine'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = db.Column(db.String(100), unique=True, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_updated = db.Column(db.DateTime(timezone=True), default=utcnow)

    building_id = db.Column(db.Integer, db.ForeignKey('building.id'), nullable=False)
    building = db.relationship("Building", back_populates="machines")

    time_slots = db.relationship("TimeSlot", back_populates="machine", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WashingMachine(name={self.name})>"
