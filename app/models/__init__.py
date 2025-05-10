# app/models/__init__.py
# Author: Indrajit Ghosh
# Created On: May 10, 2025
#
from .user import User
from .washingmachine import WashingMachine
from .booking import TimeSlot, Booking

__all__ = ['User', 'WashingMachine', 'TimeSlot', 'Booking']
