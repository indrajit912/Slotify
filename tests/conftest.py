# tests/conftest.py
# Author: Indrajit Ghosh
# Created On: May 19, 2025
# 
import pytest
from slotify import create_app
from app.extensions import db
from config_test import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
