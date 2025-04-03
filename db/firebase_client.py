from app.config.firebase import get_firestore_client, get_auth_client
from firebase_admin import firestore, auth
from typing import Dict, List, Any, Optional, Union
import datetime

# Firestore collection names
USERS_COLLECTION = "users"
TRAINERS_COLLECTION = "trainers"
GYM_ADMINS_COLLECTION = "gymAdmins"
POSTS_COLLECTION = "posts"
COMMENTS_COLLECTION = "comments"
CONNECTIONS_COLLECTION = "connections"
CONVERSATIONS_COLLECTION = "conversations"
MESSAGES_COLLECTION = "messages"
NOTIFICATIONS_COLLECTION = "notifications"
MILESTONES_COLLECTION = "milestones"
ACHIEVEMENTS_COLLECTION = "achievements"

async def get_user_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    """
    Get user from Firestore by UID
    
    Args:
        uid: User ID from Firebase Auth
        
    Returns:
        User data or None if not found
    """
    db = get_firestore_client()
    
    # Check in users collection
    user_doc = db.collection(USERS_COLLECTION).document(uid).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_data["uid"] = uid
        return user_data
    
    # Check in trainers collection
    trainer_doc = db.collection(TRAINERS_COLLECTION).document(uid).get()
    if trainer_doc.exists:
        trainer_data = trainer_doc.to_dict()
        trainer_data["uid"] = uid
        trainer_data["role"] = "trainer"
        return trainer_data
    
    # Check in gym admins collection
    admin_doc = db.collection(GYM_ADMINS_COLLECTION).document(uid).get()
    if admin_doc.exists:
        admin_data = admin_doc.to_dict()
        admin_data["uid"] = uid
        admin_data["role"] = "gym_admin"
        return admin_data
    
    return None

async def update_user_status(uid: str, is_online: bool) -> bool:
    """
    Update user's online status
    
    Args:
        uid: User ID
        is_online: Whether the user is online
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    try:
        # Check which collection the user is in
        user_doc = db.collection(USERS_COLLECTION).document(uid).get()
        if user_doc.exists:
            collection = USERS_COLLECTION
        else:
            trainer_doc = db.collection(TRAINERS_COLLECTION).document(uid).get()
            if trainer_doc.exists:
                collection = TRAINERS_COLLECTION
            else:
                admin_doc = db.collection(GYM_ADMINS_COLLECTION).document(uid).get()
                if admin_doc.exists:
                    collection = GYM_ADMINS_COLLECTION
                else:
                    return False  # User not found
        
        # Update the user's status
        db.collection(collection).document(uid).update({
            "isOnline": is_online,
            "lastActive": firestore.SERVER_TIMESTAMP,
            "status": "available" if is_online else "offline"
        })
        
        return True
    except Exception as e:
        print(f"Error updating user status: {e}")
        return False

async def get_active_users() -> List[Dict[str, Any]]:
    """
    Get all active users
    
    Returns:
        List of active users
    """
    db = get_firestore_client()
    active_users = []
    
    # Get active regular users
    users_query = db.collection(USERS_COLLECTION).where("isOnline", "==", True).stream()
    for doc in users_query:
        user_data = doc.to_dict()
        user_data["uid"] = doc.id
        user_data["role"] = "user"
        active_users.append(user_data)
    
    # Get active trainers
    trainers_query = db.collection(TRAINERS_COLLECTION).where("isOnline", "==", True).stream()
    for doc in trainers_query:
        trainer_data = doc.to_dict()
        trainer_data["uid"] = doc.id
        trainer_data["role"] = "trainer"
        active_users.append(trainer_data)
    
    # Get active gym admins
    admins_query = db.collection(GYM_ADMINS_COLLECTION).where("isOnline", "==", True).stream()
    for doc in admins_query:
        admin_data = doc.to_dict()
        admin_data["uid"] = doc.id
        admin_data["role"] = "gym_admin"
        active_users.append(admin_data)
    
    return active_users

async def create_user(user_data: Dict[str, Any], role: str = "user") -> Optional[str]:
    """
    Create a new user in Firestore
    
    Args:
        user_data: User data to create
        role: User role (user, trainer, gym_admin)
        
    Returns:
        User ID if successful, None otherwise
    """
    db = get_firestore_client()
    try:
        uid = user_data.get("uid")
        if not uid:
            return None
        
        # Determine which collection to use based on role
        if role == "trainer":
            collection = TRAINERS_COLLECTION
        elif role == "gym_admin":
            collection = GYM_ADMINS_COLLECTION
        else:
            collection = USERS_COLLECTION
        
        # Add created timestamp
        user_data["createdAt"] = firestore.SERVER_TIMESTAMP
        user_data["updatedAt"] = firestore.SERVER_TIMESTAMP
        user_data["isOnline"] = True
        user_data["lastActive"] = firestore.SERVER_TIMESTAMP
        
        # Create user document
        db.collection(collection).document(uid).set(user_data)
        
        return uid
    except Exception as e:
        print(f"Error creating user: {e}")
        return None