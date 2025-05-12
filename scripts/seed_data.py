"""
seed_data.py

Author: Indrajit Ghosh
Created On: May 12, 2025

This script seeds the Slotify database with sample data for development and testing purposes.
It creates a few buildings and populates them with randomly generated Indian users using Faker.

Usage:
    From the project root directory run the following
    $ python -m scripts.seed_data

Requirements:
    - Flask app must be properly configured and importable via `create_app()`
    - Database models for Building and User must be defined
    - Faker library must be installed: pip install faker

Note:
    All test users are assigned the password: 'test@123'
"""
import uuid
import random
from datetime import date, timedelta
from faker import Faker
from app import create_app
from app.extensions import db
from app.models.building import Building
from app.models.booking import Booking, TimeSlot
from app.models.washingmachine import WashingMachine
from app.models.user import User

app = create_app()
faker = Faker("en_IN")  # Use Indian locale


def seed_data():
    with app.app_context():

        # Create sample buildings
        building_names = ["Aryabhata", "Bhaskara", "Ramanujan", "Vikram Sarabhai"]
        buildings = []
        for name in building_names:
            b = Building(name=name, uuid=uuid.uuid4().hex)
            db.session.add(b)
            buildings.append(b)
        db.session.commit()

        print("Added buildings.")

        # Add machines to buildings
        machine_labels = ["A", "B", "C", "D"]
        machines = []
        for building in buildings:
            num_machines = faker.random_int(min=2, max=4)
            for i in range(num_machines):
                label = machine_labels[i % len(machine_labels)]
                machine_name = f"{building.name} - Machine {label}"

                machine = WashingMachine(
                    name=machine_name,
                    uuid=uuid.uuid4().hex,
                    building_id=building.id
                )
                db.session.add(machine)
                machines.append(machine)
        db.session.commit()

        print("Added washing machines.")

        # Create 4 time slots per machine
        default_slots = [
            (1, "06:00–08:00"),
            (2, "08:00–10:00"),
            (3, "10:00–12:00"),
            (4, "12:00–14:00")
        ]

        for machine in machines:
            for slot_num, time_range in default_slots:
                slot = TimeSlot(
                    uuid=uuid.uuid4().hex,
                    machine_id=machine.id,
                    slot_number=slot_num,
                    time_range=time_range
                )
                db.session.add(slot)
        db.session.commit()

        print("Created time slots for each machine.")

        # Generate users
        roles = ["user", "admin", "superadmin"]
        users = []
        for i in range(20):
            fullname = faker.name()
            username = f"user{i+1}"
            email = faker.email()
            role = roles[i % len(roles)]
            building = buildings[i % len(buildings)]

            user = User(
                username=username,
                fullname=fullname,
                email=email,
                role=role,
                building_id=building.id,
                uuid=uuid.uuid4().hex
            )
            user.set_hashed_password("test@123")
            db.session.add(user)
            users.append(user)

        db.session.commit()
        print("Added 20 Indian users.")

        # Make bookings for some users
        all_slots = TimeSlot.query.all()
        booking_days = [date.today() + timedelta(days=i) for i in range(3)]  # today + next 2 days

        for user in users[:10]:  # First 10 users get bookings
            for _ in range(random.randint(1, 3)):  # 1 to 3 bookings per user
                chosen_slot = random.choice(all_slots)
                chosen_date = random.choice(booking_days)

                # Avoid duplicate bookings on same slot & day
                if not Booking.query.filter_by(time_slot_id=chosen_slot.id, date=chosen_date).first():
                    booking = Booking(
                        uuid=uuid.uuid4().hex,
                        user_id=user.id,
                        time_slot_id=chosen_slot.id,
                        date=chosen_date
                    )
                    db.session.add(booking)

        db.session.commit()
        print("Created sample bookings for first 10 users.")



if __name__ == "__main__":
    seed_data()
