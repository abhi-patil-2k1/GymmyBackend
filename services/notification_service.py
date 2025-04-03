from typing import Dict, List, Any, Optional, Tuple
from app.db.firebase_client import get_user_by_uid
from app.config.firebase import get_firestore_client
from firebase_admin import firestore
import uuid
from datetime import datetime

# Collection names
NOTIFICATIONS_COLLECTION = "notifications"

async def get_notifications(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get user's notifications
    
    Args:
        user_id: User ID
        skip: Number of notifications to skip
        limit: Maximum number of notifications to return
        unread_only: Whether to return only unread notifications
        
    Returns:
        Tuple of (notifications list, unread count)
    """
    db = get_firestore_client()
    
    try:
        # Query notifications for the user
        notifications_query = db.collection(NOTIFICATIONS_COLLECTION).where("userId", "==", user_id)
        
        # Filter unread if requested
        if unread_only:
            notifications_query = notifications_query.where("isRead", "==", False)
        
        # Order by creation time
        notifications_query = notifications_query.order_by("createdAt", direction=firestore.Query.DESCENDING)
        
        # Get all notifications for counting
        notifications_docs = list(notifications_query.stream())
        
        # Count unread
        unread_count = sum(1 for doc in notifications_docs if not doc.to_dict().get("isRead", False))
        
        # Apply pagination
        paginated_docs = notifications_docs[skip:skip + limit]
        
        # Format notifications
        notifications = []
        for doc in paginated_docs:
            notification_data = doc.to_dict()
            notification_data["id"] = doc.id
            notifications.append(notification_data)
        
        return notifications, unread_count
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return [], 0

async def get_unread_count(user_id: str) -> int:
    """
    Get count of unread notifications
    
    Args:
        user_id: User ID
        
    Returns:
        Count of unread notifications
    """
    db = get_firestore_client()
    
    try:
        # Query unread notifications for the user
        notifications_query = db.collection(NOTIFICATIONS_COLLECTION).where(
            "userId", "==", user_id
        ).where("isRead", "==", False)
        
        # Count results
        unread_count = len(list(notifications_query.stream()))
        
        return unread_count
    except Exception as e:
        print(f"Error getting unread count: {e}")
        return 0

async def get_notification(notification_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific notification
    
    Args:
        notification_id: Notification ID
        user_id: User ID
        
    Returns:
        Notification data or None if not found
    """
    db = get_firestore_client()
    
    try:
        notification_doc = db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).get()
        if not notification_doc.exists:
            return None
            
        notification_data = notification_doc.to_dict()
        
        # Check if notification belongs to user
        if notification_data.get("userId") != user_id:
            return None
            
        notification_data["id"] = notification_id
        return notification_data
    except Exception as e:
        print(f"Error getting notification: {e}")
        return None

async def update_notification(
    notification_id: str,
    user_id: str,
    notification_update: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update a notification
    
    Args:
        notification_id: Notification ID
        user_id: User ID
        notification_update: Notification data to update
        
    Returns:
        Updated notification or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Check if notification exists and belongs to user
        notification = await get_notification(notification_id, user_id)
        if not notification:
            return None
        
        # Update notification
        db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).update(notification_update)
        
        # Get updated notification
        updated_notification = await get_notification(notification_id, user_id)
        return updated_notification
    except Exception as e:
        print(f"Error updating notification: {e}")
        return None

async def mark_all_as_read(user_id: str) -> List[Dict[str, Any]]:
    """
    Mark all notifications as read
    
    Args:
        user_id: User ID
        
    Returns:
        List of updated notifications
    """
    db = get_firestore_client()
    
    try:
        # Query unread notifications for the user
        notifications_query = db.collection(NOTIFICATIONS_COLLECTION).where(
            "userId", "==", user_id
        ).where("isRead", "==", False)
        
        batch = db.batch()
        
        # Update each notification
        for doc in notifications_query.stream():
            doc_ref = db.collection(NOTIFICATIONS_COLLECTION).document(doc.id)
            batch.update(doc_ref, {"isRead": True})
        
        # Commit batch update
        batch.commit()
        
        # Get updated notifications
        notifications_query = db.collection(NOTIFICATIONS_COLLECTION).where(
            "userId", "==", user_id
        ).order_by("createdAt", direction=firestore.Query.DESCENDING).limit(20)
        
        notifications = []
        for doc in notifications_query.stream():
            notification_data = doc.to_dict()
            notification_data["id"] = doc.id
            notifications.append(notification_data)
        
        return notifications
    except Exception as e:
        print(f"Error marking all notifications as read: {e}")
        return []

async def delete_notification(notification_id: str, user_id: str) -> bool:
    """
    Delete a notification
    
    Args:
        notification_id: Notification ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if notification exists and belongs to user
        notification = await get_notification(notification_id, user_id)
        if not notification:
            return False
        
        # Delete notification
        db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).delete()
        
        return True
    except Exception as e:
        print(f"Error deleting notification: {e}")
        return False

async def delete_all_notifications(user_id: str) -> bool:
    """
    Delete all notifications for a user
    
    Args:
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Query notifications for the user
        notifications_query = db.collection(NOTIFICATIONS_COLLECTION).where("userId", "==", user_id)
        
        batch = db.batch()
        
        # Delete each notification
        for doc in notifications_query.stream():
            doc_ref = db.collection(NOTIFICATIONS_COLLECTION).document(doc.id)
            batch.delete(doc_ref)
        
        # Commit batch delete
        batch.commit()
        
        return True
    except Exception as e:
        print(f"Error deleting all notifications: {e}")
        return False

async def create_notification(
    user_id: str,
    notification_type: str,
    message: str,
    source_user_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new notification
    
    Args:
        user_id: User ID to notify
        notification_type: Type of notification
        message: Notification message
        source_user_id: Source user ID (if applicable)
        data: Additional data
        
    Returns:
        Created notification or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Generate unique ID for notification
        notification_id = str(uuid.uuid4())
        
        # Get source user data if provided
        source_user_name = None
        source_user_photo = None
        
        if source_user_id:
            source_user = await get_user_by_uid(source_user_id)
            if source_user:
                source_user_name = source_user.get("displayName", "")
                source_user_photo = source_user.get("photoURL")
        
        # Create notification document
        notification = {
            "userId": user_id,
            "type": notification_type,
            "message": message,
            "isRead": False,
            "createdAt": firestore.SERVER_TIMESTAMP
        }
        
        if source_user_id:
            notification["sourceUserId"] = source_user_id
            notification["sourceUserName"] = source_user_name
            notification["sourceUserPhoto"] = source_user_photo
        
        if data:
            notification["data"] = data
        
        # Create notification in Firestore
        db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification)
        
        # Return notification with ID
        notification["id"] = notification_id
        notification["createdAt"] = datetime.now()  # Placeholder for SERVER_TIMESTAMP
        
        return notification
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None