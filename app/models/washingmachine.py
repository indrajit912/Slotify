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
    code = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available") # e.g., "available", "maintenance", "offline"

    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    last_updated = db.Column(db.DateTime(timezone=True), default=utcnow)

    building_id = db.Column(db.Integer, db.ForeignKey('building.id'), nullable=False)
    building = db.relationship("Building", back_populates="machines")

    time_slots = db.relationship("TimeSlot", back_populates="machine", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WashingMachine(name={self.name}, code={self.code})>"
    
    def is_available(self):
        return self.status.lower() == 'available'
