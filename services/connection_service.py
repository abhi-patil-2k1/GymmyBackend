from typing import Dict, List, Any, Optional
from app.db.firebase_client import get_user_by_uid
from app.config.firebase import get_firestore_client
from firebase_admin import firestore
import uuid
from datetime import datetime

# Collection names
CONNECTIONS_COLLECTION = "connections"
NOTIFICATIONS_COLLECTION = "notifications"

async def get_connections(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    status: str = "accepted"
) -> List[Dict[str, Any]]:
    """
    Get user's connections
    
    Args:
        user_id: User ID
        skip: Number of connections to skip
        limit: Maximum number of connections to return
        status: Connection status filter
        
    Returns:
        List of connections
    """
    db = get_firestore_client()
    
    try:
        # Query connections where the user is involved
        connections_query = db.collection(CONNECTIONS_COLLECTION).where(
            "userIds", "array_contains", user_id
        ).where("status", "==", status)
        
        connections = []
        for conn_doc in connections_query.stream():
            conn_data = conn_doc.to_dict()
            
            # Determine the other user in the connection
            other_user_id = None
            for uid in conn_data.get("userIds", []):
                if uid != user_id:
                    other_user_id = uid
                    break
            
            if other_user_id:
                # Get other user's data
                other_user = await get_user_by_uid(other_user_id)
                if other_user:
                    # Create connection response
                    connection_response = {
                        "id": conn_doc.id,
                        "userId": other_user_id,
                        "status": conn_data.get("status"),
                        "displayName": other_user.get("displayName", ""),
                        "photoURL": other_user.get("photoURL"),
                        "isRequester": conn_data.get("requesterId") == user_id,
                        "message": conn_data.get("message"),
                        "createdAt": conn_data.get("createdAt")
                    }
                    connections.append(connection_response)
        
        # Sort by created time
        connections.sort(key=lambda x: x.get("createdAt", datetime.min), reverse=True)
        
        # Apply pagination
        paginated_connections = connections[skip:skip + limit]
        
        return paginated_connections
    except Exception as e:
        print(f"Error getting connections: {e}")
        return []

async def get_connection_requests(
    user_id: str,
    skip: int = 0,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get pending connection requests for the user
    
    Args:
        user_id: User ID
        skip: Number of requests to skip
        limit: Maximum number of requests to return
        
    Returns:
        List of connection requests
    """
    db = get_firestore_client()
    
    try:
        # Query connections where the user is the recipient and status is pending
        connections_query = db.collection(CONNECTIONS_COLLECTION).where(
            "recipientId", "==", user_id
        ).where("status", "==", "pending")
        
        connections = []
        for conn_doc in connections_query.stream():
            conn_data = conn_doc.to_dict()
            
            # Get requester's data
            requester_id = conn_data.get("requesterId")
            requester = await get_user_by_uid(requester_id)
            
            if requester:
                # Create connection response
                connection_response = {
                    "id": conn_doc.id,
                    "userId": requester_id,
                    "status": conn_data.get("status"),
                    "displayName": requester.get("displayName", ""),
                    "photoURL": requester.get("photoURL"),
                    "isRequester": False,  # The other user is the requester
                    "message": conn_data.get("message"),
                    "createdAt": conn_data.get("createdAt")
                }
                connections.append(connection_response)
        
        # Sort by created time
        connections.sort(key=lambda x: x.get("createdAt", datetime.min), reverse=True)
        
        # Apply pagination
        paginated_connections = connections[skip:skip + limit]
        
        return paginated_connections
    except Exception as e:
        print(f"Error getting connection requests: {e}")
        return []

async def get_connection(connection_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific connection
    
    Args:
        connection_id: Connection ID
        user_id: Current user's ID
        
    Returns:
        Connection data or None if not found
    """
    db = get_firestore_client()
    
    try:
        conn_doc = db.collection(CONNECTIONS_COLLECTION).document(connection_id).get()
        if not conn_doc.exists:
            return None
            
        conn_data = conn_doc.to_dict()
        
        # Check if user is part of this connection
        if user_id not in conn_data.get("userIds", []):
            return None
        
        # Determine the other user in the connection
        other_user_id = None
        for uid in conn_data.get("userIds", []):
            if uid != user_id:
                other_user_id = uid
                break
        
        if other_user_id:
            # Get other user's data
            other_user = await get_user_by_uid(other_user_id)
            if other_user:
                # Create connection response
                connection_response = {
                    "id": conn_doc.id,
                    "userId": other_user_id,
                    "status": conn_data.get("status"),
                    "displayName": other_user.get("displayName", ""),
                    "photoURL": other_user.get("photoURL"),
                    "isRequester": conn_data.get("requesterId") == user_id,
                    "message": conn_data.get("message"),
                    "createdAt": conn_data.get("createdAt")
                }
                return connection_response
        
        return None
    except Exception as e:
        print(f"Error getting connection: {e}")
        return None

async def send_connection_request(
    requester_id: str,
    recipient_id: str,
    message: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Send a connection request to another user
    
    Args:
        requester_id: Requester's user ID
        recipient_id: Recipient's user ID
        message: Optional message
        
    Returns:
        Connection data or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Check if users exist
        requester = await get_user_by_uid(requester_id)
        recipient = await get_user_by_uid(recipient_id)
        
        if not requester or not recipient:
            return None
        
        # Check if connection already exists
        existing_query = db.collection(CONNECTIONS_COLLECTION).where(
            "userIds", "array_contains", requester_id
        )
        
        for conn_doc in existing_query.stream():
            conn_data = conn_doc.to_dict()
            if recipient_id in conn_data.get("userIds", []):
                # Connection already exists
                status = conn_data.get("status")
                
                if status == "blocked":
                    return None  # Cannot send request if blocked
                
                # Return existing connection
                connection_response = {
                    "id": conn_doc.id,
                    "userId": recipient_id,
                    "status": status,
                    "displayName": recipient.get("displayName", ""),
                    "photoURL": recipient.get("photoURL"),
                    "isRequester": conn_data.get("requesterId") == requester_id,
                    "message": conn_data.get("message"),
                    "createdAt": conn_data.get("createdAt")
                }
                return connection_response
        
        # Create new connection
        connection_id = str(uuid.uuid4())
        timestamp = firestore.SERVER_TIMESTAMP
        
        connection_data = {
            "userIds": [requester_id, recipient_id],
            "requesterId": requester_id,
            "recipientId": recipient_id,
            "status": "pending",
            "message": message,
            "createdAt": timestamp,
            "updatedAt": timestamp
        }
        
        # Add connection to Firestore
        db.collection(CONNECTIONS_COLLECTION).document(connection_id).set(connection_data)
        
        # Create notification for recipient
        notification_id = str(uuid.uuid4())
        notification_data = {
            "userId": recipient_id,
            "type": "connection_request",
            "sourceUserId": requester_id,
            "sourceUserName": requester.get("displayName", ""),
            "sourceUserPhoto": requester.get("photoURL"),
            "message": f"{requester.get('displayName', '')} sent you a connection request",
            "data": {
                "connectionId": connection_id
            },
            "isRead": False,
            "createdAt": timestamp
        }
        
        db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification_data)
        
        # Return connection response
        connection_response = {
            "id": connection_id,
            "userId": recipient_id,
            "status": "pending",
            "displayName": recipient.get("displayName", ""),
            "photoURL": recipient.get("photoURL"),
            "isRequester": True,
            "message": message,
            "createdAt": datetime.now()  # Use current time as placeholder for SERVER_TIMESTAMP
        }
        
        return connection_response
    except Exception as e:
        print(f"Error sending connection request: {e}")
        return None

async def respond_to_connection_request(
    connection_id: str,
    user_id: str,
    action: str
) -> Optional[Dict[str, Any]]:
    """
    Respond to a connection request
    
    Args:
        connection_id: Connection ID
        user_id: Current user's ID
        action: Action to take (accept, reject, block)
        
    Returns:
        Updated connection data or None if failed
    """
    db = get_firestore_client()
    
    try:
        conn_doc = db.collection(CONNECTIONS_COLLECTION).document(connection_id).get()
        if not conn_doc.exists:
            return None
            
        conn_data = conn_doc.to_dict()
        
        # Check if user is the recipient of this request
        if conn_data.get("recipientId") != user_id:
            return None
        
        if conn_data.get("status") != "pending":
            return None  # Can only respond to pending requests
        
        # Get requester data
        requester_id = conn_data.get("requesterId")
        requester = await get_user_by_uid(requester_id)
        if not requester:
            return None
        
        # Update status based on action
        new_status = None
        if action == "accept":
            new_status = "accepted"
        elif action == "reject":
            new_status = "rejected"
        elif action == "block":
            new_status = "blocked"
        else:
            return None  # Invalid action
        
        # Update connection
        db.collection(CONNECTIONS_COLLECTION).document(connection_id).update({
            "status": new_status,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        # Create notification for requester if accepted
        if action == "accept":
            notification_id = str(uuid.uuid4())
            current_user = await get_user_by_uid(user_id)
            
            notification_data = {
                "userId": requester_id,
                "type": "connection_accepted",
                "sourceUserId": user_id,
                "sourceUserName": current_user.get("displayName", ""),
                "sourceUserPhoto": current_user.get("photoURL"),
                "message": f"{current_user.get('displayName', '')} accepted your connection request",
                "data": {
                    "connectionId": connection_id
                },
                "isRead": False,
                "createdAt": firestore.SERVER_TIMESTAMP
            }
            
            db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification_data)
        
        # Return updated connection
        connection_response = {
            "id": connection_id,
            "userId": requester_id,
            "status": new_status,
            "displayName": requester.get("displayName", ""),
            "photoURL": requester.get("photoURL"),
            "isRequester": False,
            "message": conn_data.get("message"),
            "createdAt": conn_data.get("createdAt")
        }
        
        return connection_response
    except Exception as e:
        print(f"Error responding to connection request: {e}")
        return None

async def remove_connection(connection_id: str, user_id: str) -> bool:
    """
    Remove a connection
    
    Args:
        connection_id: Connection ID
        user_id: Current user's ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        conn_doc = db.collection(CONNECTIONS_COLLECTION).document(connection_id).get()
        if not conn_doc.exists:
            return False
            
        conn_data = conn_doc.to_dict()
        
        # Check if user is part of this connection
        if user_id not in conn_data.get("userIds", []):
            return False
        
        # Delete connection
        db.collection(CONNECTIONS_COLLECTION).document(connection_id).delete()
        
        return True
    except Exception as e:
        print(f"Error removing connection: {e}")
        return False

async def check_connection_status(user_id: str, other_user_id: str) -> str:
    """
    Check connection status between two users
    
    Args:
        user_id: Current user's ID
        other_user_id: Other user's ID
        
    Returns:
        Connection status (none, pending, accepted, rejected, blocked)
    """
    db = get_firestore_client()
    
    try:
        # Query connections where both users are involved
        connections_query = db.collection(CONNECTIONS_COLLECTION).where(
            "userIds", "array_contains", user_id
        )
        
        for conn_doc in connections_query.stream():
            conn_data = conn_doc.to_dict()
            if other_user_id in conn_data.get("userIds", []):
                # Found connection
                status = conn_data.get("status")
                
                # If pending, check if user is the requester or recipient
                if status == "pending":
                    if conn_data.get("requesterId") == user_id:
                        return "pending_sent"
                    else:
                        return "pending_received"
                
                return status
        
        return "none"  # No connection found
    except Exception as e:
        print(f"Error checking connection status: {e}")
        return "none"