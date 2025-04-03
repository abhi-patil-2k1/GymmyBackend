import firebase_admin
from firebase_admin import credentials, auth, firestore
from typing import Optional
from app.config.settings import settings
import os

def initialize_firebase_app() -> Optional[firebase_admin.App]:
    """
    Initialize Firebase Admin SDK
    """
    try:
        # Check if app is already initialized
        try:
            return firebase_admin.get_app()
        except ValueError:
            # App not initialized yet
            pass

        # Use service account credentials from environment or file
        if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
            # Use JSON content from environment variable
            import json
            import tempfile
            
            service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            
            # Create a temporary file with the service account JSON
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                json.dump(service_account_info, temp_file)
                temp_path = temp_file.name
            
            cred = credentials.Certificate(temp_path)
            
            # Remove the temporary file after loading
            os.unlink(temp_path)
        else:
            # Use file path
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        
        # Initialize app with credential
        firebase_app = firebase_admin.initialize_app(cred, {
            'storageBucket': settings.FIREBASE_STORAGE_BUCKET
        })
        
        return firebase_app
    except Exception as e:
        print(f"Failed to initialize Firebase app: {e}")
        raise

def get_auth_client():
    """
    Get Firebase Auth client
    """
    initialize_firebase_app()
    return auth

def get_firestore_client():
    """
    Get Firestore client
    """
    initialize_firebase_app()
    return firestore.client()