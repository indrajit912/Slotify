# app/services/__init__.py
#
# Author: Indrajit Ghosh
# Created On: May 11, 2025
#
# Service layer initializer for Slotify.

# This package contains core business logic functions for the Slotify app.
# Each service module encapsulates domain-specific operations and can be
# used across views, APIs, and CLI commands.

# Modules:
#     - user_service.py: User-related operations.
#     - washing_machine_service.py: Washing machine management.
#     - booking_service.py: Slot booking and cancellation logic.
#
# Use these in the other part of the app as following:
#       from app.services import create_user, book_slot
# 
from .user_service import *
from .booking_service import *
from .washing_machine_service import *

__all__ = [
    "create_user",
    "get_user_by_uuid",
    "get_user_by_email",
    "get_user_by_username",
    "update_user_by_uuid",
    "delete_user_by_uuid",
    "create_washing_machine",
    "get_all_machines",
    "delete_washing_machine_by_uuid",
    "get_machine_monthly_slots",
    "get_time_slot_by_uuid",
    "book_slot",
    "cancel_booking",
    "get_user_bookings"
]
