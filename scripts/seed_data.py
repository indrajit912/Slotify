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
from datetime import date, timedelta
from faker import Faker
from app import create_app
from app.extensions import db
from app.models.booking import TimeSlot
from app.services import (
    create_building,
    create_new_course,
    create_user,
    create_washing_machine,
    book_slot
)

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
        # Create sample buildings
        building_names = ["Aryabhata", "Bhaskara", "Ramanujan", "Vikram Sarabhai"]
        buildings = []
        for name in building_names:
            code = name.lower().replace(" ", "_")  # e.g., "vikram_sarabhai"
            try:
                b = create_building(name=name, code=code)
                buildings.append(b)
            except ValueError as e:
                print(f"⚠️ Skipping building {name}: {e}")
        print("✅ Added buildings.")

        # Create sample courses
        courses_data = [
            {"code": "MTECHAI", "name": "Master of Technology in Artificial Intelligence", "level": "PG", "department": "Computer Science", "short_name": "MTech AI", "duration_years": 2},
            {"code": "MSCMATHS", "name": "Master of Science in Mathematics", "level": "PG", "department": "Mathematics", "short_name": "MSc Maths", "duration_years": 2},
            {"code": "PHDCS", "name": "Doctor of Philosophy in Computer Science", "level": "PhD", "department": "Computer Science", "short_name": "PhD CS", "duration_years": 5},
            {"code": "BSCSTATS", "name": "Bachelor of Science in Statistics", "level": "UG", "department": "Statistics", "short_name": "BSc Stats", "duration_years": 3},
            {"code": "IMSTAT", "name": "Integrated Master of Statistics", "level": "UG", "department": "Statistics", "short_name": "Integrated MStat", "duration_years": 5},
        ]
        courses = []
        for cd in courses_data:
            try:
                course = create_new_course(**cd)
                courses.append(course)
            except ValueError as e:
                print(f"⚠️ Skipping course {cd['code']}: {e}")
        print("✅ Added courses.")

        # Add washing machines with default time slots
        machine_labels = ["A", "B", "C", "D"]
        machines = []
        for b in buildings:
            num_machines = faker.random_int(min=2, max=4)
            for i in range(num_machines):
                label = machine_labels[i % len(machine_labels)]
                machine_name = f"{b.name} - Machine {label}"
                machine_code = f"{b.name[:3].upper()}{label}{i+1}"  # e.g., 'ARYA1'

                default_slots = [
                    {"slot_number": 1, "time_range": "06:00–08:00"},
                    {"slot_number": 2, "time_range": "08:00–10:00"},
                    {"slot_number": 3, "time_range": "10:00–12:00"},
                    {"slot_number": 4, "time_range": "12:00–14:00"},
                ]
                try:
                    machine = create_washing_machine(
                        name=machine_name,
                        code=machine_code,
                        building_uuid=str(b.uuid),
                        time_slots=default_slots
                    )
                    machines.append(machine)
                except ValueError as e:
                    print(f"⚠️ Skipping machine {machine_code}: {e}")
        print("✅ Added washing machines with time slots.")

        # Create users
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
                    course_uuid=str(course.uuid)
                )
                users.append(user)
            except ValueError as e:
                print(f"⚠️ Skipping user {username}: {e}")
        print("✅ Added 20 Indian users.")

        # Make sample bookings
        all_slots = TimeSlot.query.all()
        booking_days = [date.today() + timedelta(days=i) for i in range(3)]

        for user in users[:10]:  # First 10 users get bookings
            for _ in range(random.randint(1, 3)):
                chosen_slot = random.choice(all_slots)
                chosen_date = random.choice(booking_days)
                try:
                    book_slot(str(user.uuid), str(chosen_slot.uuid), chosen_date)
                except Exception as e:
                    print(f"⚠️ Could not book slot for {user.username} on {chosen_date}: {e}")
        print("✅ Created sample bookings for first 10 users.")


if __name__ == "__main__":
    seed_data()
