"""
test_user_service.py

Unit tests for the user_service module of Slotify.

Tests cover user creation, uniqueness constraints, update operations,
last_seen updates, and user deletion.

Run these tests with pytest.
"""

import pytest
from app.services import (
    create_user, get_user_by_email, get_user_by_username, update_user_by_uuid,
    update_user_last_seen, delete_user_by_uuid
)
from app.services.building_service import create_building
from app.extensions import db
from app.models.user import User

def test_create_user(app):
    with app.app_context():
        building = create_building(name="Test Building", code="TB01")

        user = create_user(
            username="testuser",
            email="testuser@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            building_uuid=building.uuid
        )

        assert user is not None
        assert user.username == "testuser"
        assert user.email == "testuser@example.com"
        assert user.building_id == building.id


def test_create_user_duplicate_email(app):
    with app.app_context():
        building = create_building(name="Building2", code="B002")
        user1 = create_user(
            username="user1",
            email="dupemail@example.com",
            password="pwd123",
            first_name="First",
            last_name="User",
            building_uuid=building.uuid
        )

        with pytest.raises(ValueError) as e:
            create_user(
                username="user2",
                email="dupemail@example.com",
                password="pwd456",
                first_name="Second",
                last_name="User",
                building_uuid=building.uuid
            )
        assert "Email already registered" in str(e.value)


def test_create_user_duplicate_username(app):
    with app.app_context():
        building = create_building(name="Building3", code="B003")
        user1 = create_user(
            username="dupuser",
            email="user1@example.com",
            password="pwd123",
            first_name="First",
            last_name="User",
            building_uuid=building.uuid
        )

        with pytest.raises(ValueError) as e:
            create_user(
                username="dupuser",
                email="user2@example.com",
                password="pwd456",
                first_name="Second",
                last_name="User",
                building_uuid=building.uuid
            )
        assert "Username already taken" in str(e.value)


def test_create_user_invalid_building(app):
    with app.app_context():
        invalid_uuid = "invalid-uuid-1234"
        with pytest.raises(ValueError) as e:
            create_user(
                username="invalidbuildinguser",
                email="invalid@example.com",
                password="pwd123",
                first_name="Invalid",
                last_name="Building",
                building_uuid=invalid_uuid
            )
        assert "No building found with UUID" in str(e.value)


def test_update_user_by_uuid_success(app):
    with app.app_context():
        building = create_building(name="UpdateBuilding", code="UB01")
        user = create_user(
            username="updatableuser",
            email="update@example.com",
            password="pwd123",
            first_name="Original",
            last_name="Name",
            building_uuid=building.uuid
        )

        updated_user = update_user_by_uuid(
            user.uuid,
            first_name="Updated",
            last_name="User",
            username="updateduser",
            email="updated@example.com"
        )

        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "User"
        assert updated_user.username == "updateduser"
        assert updated_user.email == "updated@example.com"


def test_update_user_by_uuid_duplicate_email_username(app):
    with app.app_context():
        building = create_building(name="UpdateBuilding2", code="UB02")
        user1 = create_user(
            username="userupdate1",
            email="userupdate1@example.com",
            password="pwd123",
            first_name="User",
            last_name="One",
            building_uuid=building.uuid
        )
        user2 = create_user(
            username="userupdate2",
            email="userupdate2@example.com",
            password="pwd456",
            first_name="User",
            last_name="Two",
            building_uuid=building.uuid
        )

        with pytest.raises(ValueError) as e:
            update_user_by_uuid(user2.uuid, email="userupdate1@example.com")
        assert "Email already registered" in str(e.value)

        with pytest.raises(ValueError) as e:
            update_user_by_uuid(user2.uuid, username="userupdate1")
        assert "Username already taken" in str(e.value)


def test_update_user_last_seen(app):
    with app.app_context():
        building = create_building(name="LastSeenBuilding", code="LS01")
        user = create_user(
            username="lastseenuser",
            email="lastseen@example.com",
            password="pwd123",
            first_name="Last",
            last_name="Seen",
            building_uuid=building.uuid
        )

        result = update_user_last_seen(user.uuid)
        assert result is True

        # Test with non-existent UUID
        result = update_user_last_seen("non-existent-uuid")
        assert result is False


def test_delete_user_by_uuid_success(app):
    with app.app_context():
        building = create_building(name="DeleteBuilding", code="DB01")
        user = create_user(
            username="deleteuser",
            email="delete@example.com",
            password="pwd123",
            first_name="Delete",
            last_name="User",
            building_uuid=building.uuid
        )

        result = delete_user_by_uuid(user.uuid)
        assert result is True

        # Verify user no longer exists
        deleted_user = get_user_by_email("delete@example.com")
        assert deleted_user is None


def test_delete_user_by_uuid_nonexistent(app):
    with app.app_context():
        with pytest.raises(ValueError) as e:
            delete_user_by_uuid("non-existent-uuid")
        assert "User not found" in str(e.value)
