# app/models/booking.py
# 
# Author: Indrajit Ghosh
# Created On: May 10, 2025
# 
import uuid
from app.extensions import db

class TimeSlot(db.Model):
    __tablename__ = 'timeslot'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    machine_id = db.Column(db.Integer, db.ForeignKey('washingmachine.id'), nullable=False)
    slot_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    time_range = db.Column(db.String(20), nullable=False, default="00:00-00:00")

    machine = db.relationship("WashingMachine", back_populates="time_slots")
    bookings = db.relationship("Booking", back_populates="time_slot", cascade="all, delete-orphan")


class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('timeslot.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    user = db.relationship("User", back_populates="bookings")
    time_slot = db.relationship("TimeSlot", back_populates="bookings")

    __table_args__ = (
        db.UniqueConstraint('time_slot_id', 'date', name='unique_slot_per_day'),
    )
