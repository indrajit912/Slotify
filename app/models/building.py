# app/models/building.py
# 
# Author: Indrajit Ghosh
# Created On: May 11, 2025
# 
import uuid

# Local application imports
from app.extensions import db

class Building(db.Model):
    __tablename__ = 'building'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)

    users = db.relationship("User", back_populates="building")
    machines = db.relationship("WashingMachine", back_populates="building")

    def __repr__(self):
        return f"<Building(name={self.name}, code={self.code})>"

    def to_json(self):
        """
        Serialize Building to JSON-friendly dict.
        Machines and users are NOT included by default to avoid recursion and large payload.
        """
        return {
            "uuid": self.uuid,
            "name": self.name,
            "code": self.code
        }

    @classmethod
    def from_json(cls, data):
        """
        Create Building instance from JSON dict.
        """
        return cls(
            uuid=data.get("uuid"),
            name=data["name"],
            code=data["code"]
        )
