"""
app/main/routes.py

This module defines the routes and views for the Flask web application.

Author: Indrajit Ghosh
Created on: Jun 05, 2025
"""
from flask import render_template

from . import main_bp
from app.api.v1.auth_api import register
from app.api.v1.db_management_api import export_data, import_data
from app.api.v1.building_api import list_buildings
from app.api.v1.user_api import list_users, update_user, search_user_api

@main_bp.route('/api/docs')
def api_doc():
    api_definitions = [
        {
            'category': 'Authentication',
            'title': 'Register User',
            'method': 'POST',
            'url': '/api/v1/auth/register',
            'docstring': register.__doc__
        },
        {
            'category': 'User Management',
            'title': 'List or Get Users',
            'method': 'GET',
            'urls': ['/api/v1/users/', '/api/v1/users/<uuid>'],
            'docstring': list_users.__doc__
        },
        {
            'category': 'User Management',
            'title': 'Update User',
            'method': 'PUT',
            'url': '/api/v1/users/<user_uuid>',
            'docstring': update_user.__doc__
        },
        {
            'category': 'User Management',
            'title': 'Search Users',
            'method': 'GET',
            'url': '/api/v1/users/search',
            'docstring': search_user_api.__doc__
        },
        {
            'category': 'Building Management',
            'title': 'Get Buildings',
            'method': 'GET',
            'urls': ['/api/v1/buildings', '/api/v1/buildings/<building_uuid>'],
            'docstring': list_buildings.__doc__
        },
        {
            'category': 'Database Management',
            'title': 'Export Data',
            'method': 'GET',
            'url': '/api/v1/export',
            'docstring': export_data.__doc__
        },
        {
            'category': 'Database Management',
            'title': 'Import Data',
            'method': 'POST',
            'url': '/api/v1/import',
            'docstring': import_data.__doc__
        },
    ]

    # Group by category
    grouped_apis = {}
    for api in api_definitions:
        cat = api['category']
        grouped_apis.setdefault(cat, []).append(api)

    return render_template('api_documentation.html', grouped_apis=grouped_apis)