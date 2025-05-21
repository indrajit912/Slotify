"""
config_test.py

Author: Indrajit Ghosh
Created on: May 19, 2025
"""

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory DB for testing
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False  # Disable CSRF in tests
    SECRET_KEY = "test-secret-key"
