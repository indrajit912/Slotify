"""
seed_data.py

Author: Indrajit Ghosh
Created On: May 12, 2025

This script seeds the Slotify database with sample data for development and testing purposes.
It creates a few buildings, courses, and populates them with randomly generated Indian users using Faker.

Usage:
    From the project root directory run the following
    $ python -m scripts.seed_data

Requirements:
    - Flask app must be properly configured and importable via `create_app()`
    - Database models for Building, User, Course, WashingMachine, TimeSlot, Booking must be defined
    - Faker library must be installed: pip install faker

Note:
    All test users are assigned the password: 'test@123'
"""

import random
from faker import Faker
from app import create_app
from app.models.building import Building
from app.models.course import Course
from app.services import create_user

app = create_app()
faker = Faker("en_IN")  # Use Indian locale


def split_name(full_name):
    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], "", ""
    elif len(parts) == 2:
        return parts[0], "", parts[1]
    else:
        return parts[0], " ".join(parts[1:-1]), parts[-1]

def seed_data():
    with app.app_context():
        # Fetch all buildings and courses
        buildings = Building.query.all()
        courses = Course.query.all()

        if not buildings or not courses:
            print("❌ Cannot seed users: No buildings or courses found.")
            return

        roles = ["user", "admin"]
        users = []

        for i in range(20):
            full_name = faker.name()
            first_name, middle_name, last_name = split_name(full_name)
            username = f"user{i+1}"
            email = faker.email()
            role = roles[i % len(roles)]
            building = buildings[i % len(buildings)]
            course = courses[i % len(courses)]
            contact_no = faker.phone_number()
            room_no = str(random.randint(100, 599))

            try:
                user = create_user(
                    username=username,
                    first_name=first_name,
                    middle_name=middle_name or None,
                    last_name=last_name or "Singh",
                    email=email,
                    password="test@123",
                    role=role,
                    building_uuid=str(building.uuid),
                    course_uuid=str(course.uuid), 
                    contact_no=contact_no,
                    room_no=room_no
                )
                users.append(user)
            except ValueError as e:
                print(f"⚠️ Skipping user {username}: {e}")
        
        print(f"✅ Added {len(users)} Indian users.")


if __name__ == "__main__":
    seed_data()
