"""
app/main/routes.py

This module defines the routes and views for the Flask web application.

Author: Indrajit Ghosh
Created on: May 10, 2025
"""
import logging

from flask import render_template

from . import main_bp

logger = logging.getLogger(__name__)


#######################################################
#                      Homepage
#######################################################
@main_bp.route('/')
def index():
    logger.info("Visited homepage.")
    return render_template("index.html")