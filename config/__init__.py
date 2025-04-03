"""
Configuration module for the GymBuddy API
"""

# Import settings for global access
from app.config.settings import settings
from app.config.firebase import initialize_firebase_app

# Initialize Firebase
firebase_app = initialize_firebase_app()