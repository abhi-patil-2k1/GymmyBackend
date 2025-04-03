from typing import Dict, List, Any, Optional
from app.db.firebase_client import (
    get_user_by_uid, 
    get_active_users as get_active_users_db,
    update_user_status, 
    create_user,
    USERS_COLLECTION
)
from app.config.firebase import get_firestore_client
from firebase_admin import firestore
import re

async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by ID
    
    Args:
        user_id: User ID
        
    Returns:
        User data or None if not found
    """
    return await get_user_by_uid(user_id)

async def update_user(user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a user's profile
    
    Args:
        user_id: User ID
        user_data: User data to update
        
    Returns:
        Updated user data or None if failed
    """
    db = get_firestore_client()
    try:
        # First check if the user exists
        user = await get_user_by_uid(user_id)
        if not user:
            return None
            
        # Determine which collection based on role
        collection = USERS_COLLECTION
        if user.get("role") == "trainer":
            collection = "trainers"
        elif user.get("role") == "gym_admin":
            collection = "gymAdmins"
        
        # Add updated timestamp
        user_data["updatedAt"] = firestore.SERVER_TIMESTAMP
        
        # Update user document
        db.collection(collection).document(user_id).update(user_data)
        
        # Get updated user
        updated_user = await get_user_by_uid(user_id)
        return updated_user
    except Exception as e:
        print(f"Error updating user: {e}")
        return None

async def get_active_users(skip: int = 0, limit: int = 20, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all active users
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        search: Optional search query
        
    Returns:
        List of active users
    """
    active_users = await get_active_users_db()
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        active_users = [
            user for user in active_users
            if search_lower in user.get("displayName", "").lower() or
            search_lower in user.get("email", "").lower() or
            any(search_lower in interest.lower() for interest in user.get("interests", []))
        ]
    
    # Apply pagination
    paginated_users = active_users[skip:skip + limit]
    
    return paginated_users

async def list_users(
    skip: int = 0, 
    limit: int = 20, 
    search: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    interests: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    List users with optional filtering
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        search: Optional search query
        filters: Optional filters
        interests: Optional list of interests to filter by
        
    Returns:
        List of users
    """
    db = get_firestore_client()
    
    # Start with base query
    query = db.collection(USERS_COLLECTION)
    
    # Apply filters if provided
    if filters:
        for key, value in filters.items():
            if value is not None:
                query = query.where(key, "==", value)
    
    # Execute query
    results = query.stream()
    users = []
    
    for doc in results:
        user_data = doc.to_dict()
        user_data["uid"] = doc.id
        users.append(user_data)
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        users = [
            user for user in users
            if search_lower in user.get("displayName", "").lower() or
            search_lower in user.get("email", "").lower() or
            any(search_lower in interest.lower() for interest in user.get("interests", []))
        ]
    
    # Apply interests filter if provided
    if interests:
        users = [
            user for user in users
            if any(interest in user.get("interests", []) for interest in interests)
        ]
    
    # Sort by online status first, then by name
    users.sort(key=lambda x: (not x.get("isOnline", False), x.get("displayName", "")))
    
    # Apply pagination
    paginated_users = users[skip:skip + limit]
    
    return paginated_users

async def get_user_stats(user_id: str) -> Dict[str, Any]:
    """
    Get a user's statistics
    
    Args:
        user_id: User ID
        
    Returns:
        User statistics
    """
    db = get_firestore_client()
    
    # Get post count
    posts_query = db.collection("posts").where("userId", "==", user_id).stream()
    post_count = sum(1 for _ in posts_query)
    
    # Get connection count
    connections_query = db.collection("connections").where("status", "==", "accepted").where("userIds", "array_contains", user_id).stream()
    connection_count = sum(1 for _ in connections_query)
    
    # Get workout count
    workouts_query = db.collection("workouts").where("userId", "==", user_id).stream()
    workout_count = sum(1 for _ in workouts_query)
    
    # Get user for level and achievements
    user = await get_user_by_uid(user_id)
    level = user.get("level", 1) if user else 1
    achievements = len(user.get("achievements", [])) if user else 0
    
    return {
        "posts": post_count,
        "connections": connection_count,
        "workouts": workout_count,
        "level": level,
        "achievements": achievements
    }