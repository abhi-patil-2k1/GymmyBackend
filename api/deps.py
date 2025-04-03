from fastapi import Depends, HTTPException, status, Header, File, UploadFile
from typing import Optional, Dict, Any, List, Generator
from app.core.security import (
    get_current_user,
    get_current_active_user,
    get_current_trainer,
    get_current_gym_admin
)
from app.config.firebase import get_firestore_client, get_auth_client

# Re-export security functions for convenience
__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_trainer",
    "get_current_gym_admin",
    "get_firestore_db",
    "get_firebase_auth",
    "validate_mime_type"
]

async def get_firestore_db() -> Any:
    """
    Get Firestore DB client
    """
    return get_firestore_client()

async def get_firebase_auth() -> Any:
    """
    Get Firebase Auth client
    """
    return get_auth_client()

async def validate_mime_type(
    file: UploadFile = File(...),
    allowed_types: Optional[List[str]] = None
) -> UploadFile:
    """
    Validate file MIME type
    
    Args:
        file: Uploaded file
        allowed_types: List of allowed MIME types
        
    Returns:
        File if valid
    
    Raises:
        HTTPException: If file type is not allowed
    """
    if not allowed_types:
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
            "application/pdf"
        ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )
    
    return file