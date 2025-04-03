from fastapi import Depends, HTTPException, status, Header
from typing import Optional, Dict, Any
from firebase_admin import auth
from app.config.firebase import get_auth_client
from app.db.firebase_client import get_user_by_uid, update_user_status
import time

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Validate Firebase ID token from Authorization header and get current user
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        Dict with user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify the Firebase ID token
        auth_client = get_auth_client()
        decoded_token = auth_client.verify_id_token(token)
        
        # Check if token is expired
        if time.time() > decoded_token.get('exp', 0):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID from token
        uid = decoded_token.get('uid')
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from Firestore
        user = await get_user_by_uid(uid)
        
        # If user doesn't exist in Firestore yet, create basic record
        if not user:
            # Get user info from Firebase Auth
            auth_user = auth_client.get_user(uid)
            
            # Basic user profile
            user = {
                "uid": uid,
                "email": auth_user.email,
                "displayName": auth_user.display_name,
                "photoURL": auth_user.photo_url,
                "role": "user",  # Default role
                "isOnline": True,
                "lastLogin": firestore.SERVER_TIMESTAMP,
            }
            
            # Will be handled by the user service to create the user in Firestore
        
        # Update user status to online
        await update_user_status(uid, True)
        
        # Add token data to user
        user["token"] = {
            "uid": uid,
            "email": decoded_token.get('email'),
            "email_verified": decoded_token.get('email_verified', False),
        }
        
        return user
        
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Revoked authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current active user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict with user information
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.get("isActive", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_current_trainer(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current trainer user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict with user information
        
    Raises:
        HTTPException: If user is not a trainer
    """
    if current_user.get("role") != "trainer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a trainer"
        )
    return current_user

async def get_current_gym_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current gym admin user
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict with user information
        
    Raises:
        HTTPException: If user is not a gym admin
    """
    if current_user.get("role") != "gym_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a gym admin"
        )
    return current_user