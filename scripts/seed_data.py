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
from app.models.building import Building
from app.models.booking import Booking, TimeSlot
from app.models.washingmachine import WashingMachine
from app.models.user import User
from app.models.course import Course

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
            b = Building(name=name, code=code)
            db.session.add(b)
            buildings.append(b)
        db.session.commit()
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
            course = Course(**cd)  # Assuming Course model assigns uuid internally
            db.session.add(course)
            courses.append(course)
        db.session.commit()
        print("✅ Added courses.")

        # Add washing machines to buildings with unique 'code'
        machine_labels = ["A", "B", "C", "D"]
        machines = []
        for b_idx, building in enumerate(buildings):
            num_machines = faker.random_int(min=2, max=4)
            for i in range(num_machines):
                label = machine_labels[i % len(machine_labels)]
                machine_name = f"{building.name} - Machine {label}"
                machine_code = f"{building.name[:3].upper()}{label}{i+1}"  # e.g., 'ARYA1'

                machine = WashingMachine(
                    name=machine_name,
                    code=machine_code,
                    building=building
                )
                db.session.add(machine)
                machines.append(machine)

        db.session.commit()
        print("✅ Added washing machines.")

        # Create 4 default time slots per machine
        default_slots = [
            (1, "06:00–08:00"),
            (2, "08:00–10:00"),
            (3, "10:00–12:00"),
            (4, "12:00–14:00")
        ]

        for machine in machines:
            for slot_num, time_range in default_slots:
                slot = TimeSlot(
                    machine=machine,  # Assuming relationship setter
                    slot_number=slot_num,
                    time_range=time_range
                )
                db.session.add(slot)
        db.session.commit()
        print("✅ Created time slots for each machine.")

        # Generate users
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

            user = User(
                username=username,
                first_name=first_name,
                middle_name=middle_name or None,
                last_name=last_name or "Singh",
                email=email,
                role=role,
                building=building,
                course=course,
                contact_no=faker.phone_number(),
                room_no=f"A-{random.randint(101, 599)}"
            )
            user.set_hashed_password("test@123")
            db.session.add(user)
            users.append(user)

        db.session.commit()
        print("✅ Added 20 Indian users.")

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
                        user=user,
                        time_slot=chosen_slot,
                        date=chosen_date
                    )
                    db.session.add(booking)

        db.session.commit()
        print("✅ Created sample bookings for first 10 users.")


if __name__ == "__main__":
    seed_data()
