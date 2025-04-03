from typing import Dict, List, Any, Optional
from app.db.firebase_client import get_user_by_uid
from app.config.firebase import get_firestore_client
from firebase_admin import firestore, storage
import uuid
from datetime import datetime

# Collection names
CONVERSATIONS_COLLECTION = "conversations"
MESSAGES_COLLECTION = "messages"
NOTIFICATIONS_COLLECTION = "notifications"

async def get_conversations(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    archived: bool = False
) -> List[Dict[str, Any]]:
    """
    Get user's conversations
    
    Args:
        user_id: User ID
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return
        archived: Whether to show archived conversations
        
    Returns:
        List of conversations
    """
    db = get_firestore_client()
    
    try:
        # Query conversations where the user is involved
        conversations_query = db.collection(CONVERSATIONS_COLLECTION).where(
            "userIds", "array_contains", user_id
        )
        
        conversations = []
        for conv_doc in conversations_query.stream():
            conv_data = conv_doc.to_dict()
            
            # Skip archived conversations based on parameter
            is_archived = conv_data.get("isArchived", {}).get(user_id, False)
            if is_archived != archived:
                continue
            
            # Determine the other user in the conversation
            other_user_id = None
            for uid in conv_data.get("userIds", []):
                if uid != user_id:
                    other_user_id = uid
                    break
            
            if other_user_id:
                # Get other user's data
                other_user = await get_user_by_uid(other_user_id)
                if other_user:
                    # Create conversation response
                    is_pinned = conv_data.get("isPinned", {}).get(user_id, False)
                    unread_count = conv_data.get("unreadCount", {}).get(user_id, 0)
                    last_message = conv_data.get("lastMessage")
                    last_message_time = conv_data.get("lastMessageTime")
                    is_own_last_message = conv_data.get("lastMessageSenderId") == user_id
                    
                    conversation_response = {
                        "id": conv_doc.id,
                        "userId": other_user_id,
                        "userName": other_user.get("displayName", ""),
                        "userPhoto": other_user.get("photoURL"),
                        "lastMessage": last_message,
                        "lastMessageTime": last_message_time,
                        "isOwnLastMessage": is_own_last_message,
                        "unreadCount": unread_count,
                        "isOnline": other_user.get("isOnline", False),
                        "isArchived": is_archived,
                        "isPinned": is_pinned
                    }
                    conversations.append(conversation_response)
        
        # Sort by pin status, then by last message time
        conversations.sort(
            key=lambda x: (
                not x.get("isPinned", False),
                x.get("lastMessageTime", datetime.min) if x.get("lastMessageTime") else datetime.min
            ),
            reverse=True
        )
        
        # Apply pagination
        paginated_conversations = conversations[skip:skip + limit]
        
        return paginated_conversations
    except Exception as e:
        print(f"Error getting conversations: {e}")
        return []

async def create_conversation(
    user_id: str,
    other_user_id: str,
    initial_message: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new conversation with another user
    
    Args:
        user_id: Current user's ID
        other_user_id: Other user's ID
        initial_message: Optional initial message
        
    Returns:
        Created conversation or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Check if users exist
        current_user = await get_user_by_uid(user_id)
        other_user = await get_user_by_uid(other_user_id)
        
        if not current_user or not other_user:
            return None
        
        # Check if conversation already exists
        conversations_query = db.collection(CONVERSATIONS_COLLECTION).where(
            "userIds", "array_contains", user_id
        )
        
        for conv_doc in conversations_query.stream():
            conv_data = conv_doc.to_dict()
            if other_user_id in conv_data.get("userIds", []):
                # Conversation already exists, get it
                conversation = await get_conversation(conv_doc.id, user_id)
                
                # If initial message is provided, send it
                if initial_message:
                    await send_message(
                        conv_doc.id,
                        user_id,
                        {"content": initial_message, "contentType": "text"}
                    )
                
                return conversation
        
        # Create new conversation
        timestamp = firestore.SERVER_TIMESTAMP
        conversation_id = str(uuid.uuid4())
        
        conversation_data = {
            "userIds": [user_id, other_user_id],
            "lastMessage": initial_message if initial_message else None,
            "lastMessageTime": timestamp if initial_message else None,
            "lastMessageSenderId": user_id if initial_message else None,
            "unreadCount": {
                user_id: 0,
                other_user_id: 1 if initial_message else 0
            },
            "isArchived": {
                user_id: False,
                other_user_id: False
            },
            "isPinned": {
                user_id: False,
                other_user_id: False
            },
            "lastRead": {
                user_id: timestamp,
                other_user_id: None
            },
            "createdAt": timestamp,
            "updatedAt": timestamp
        }
        
        # Create conversation in Firestore
        db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).set(conversation_data)
        
        # If initial message is provided, create it
        if initial_message:
            message_id = str(uuid.uuid4())
            
            message_data = {
                "conversationId": conversation_id,
                "senderId": user_id,
                "senderName": current_user.get("displayName", ""),
                "senderPhoto": current_user.get("photoURL"),
                "content": initial_message,
                "contentType": "text",
                "isRead": False,
                "createdAt": timestamp,
                "updatedAt": timestamp
            }
            
            db.collection(MESSAGES_COLLECTION).document(message_id).set(message_data)
            
            # Create notification for recipient
            notification_id = str(uuid.uuid4())
            
            notification_data = {
                "userId": other_user_id,
                "type": "message_received",
                "sourceUserId": user_id,
                "sourceUserName": current_user.get("displayName", ""),
                "sourceUserPhoto": current_user.get("photoURL"),
                "message": f"New message from {current_user.get('displayName', '')}",
                "data": {
                    "conversationId": conversation_id,
                    "messageId": message_id
                },
                "isRead": False,
                "createdAt": timestamp
            }
            
            db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification_data)
        
        # Return conversation response
        conversation_response = {
            "id": conversation_id,
            "userId": other_user_id,
            "userName": other_user.get("displayName", ""),
            "userPhoto": other_user.get("photoURL"),
            "lastMessage": initial_message,
            "lastMessageTime": datetime.now() if initial_message else None,  # Placeholder for SERVER_TIMESTAMP
            "isOwnLastMessage": initial_message is not None,
            "unreadCount": 0,
            "isOnline": other_user.get("isOnline", False),
            "isArchived": False,
            "isPinned": False
        }
        
        return conversation_response
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return None

async def get_conversation(conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific conversation
    
    Args:
        conversation_id: Conversation ID
        user_id: Current user's ID
        
    Returns:
        Conversation data or None if not found
    """
    db = get_firestore_client()
    
    try:
        conv_doc = db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).get()
        if not conv_doc.exists:
            return None
            
        conv_data = conv_doc.to_dict()
        
        # Check if user is part of this conversation
        if user_id not in conv_data.get("userIds", []):
            return None
        
        # Determine the other user in the conversation
        other_user_id = None
        for uid in conv_data.get("userIds", []):
            if uid != user_id:
                other_user_id = uid
                break
        
        if other_user_id:
            # Get other user's data
            other_user = await get_user_by_uid(other_user_id)
            if other_user:
                # Create conversation response
                is_archived = conv_data.get("isArchived", {}).get(user_id, False)
                is_pinned = conv_data.get("isPinned", {}).get(user_id, False)
                unread_count = conv_data.get("unreadCount", {}).get(user_id, 0)
                last_message = conv_data.get("lastMessage")
                last_message_time = conv_data.get("lastMessageTime")
                is_own_last_message = conv_data.get("lastMessageSenderId") == user_id
                
                conversation_response = {
                    "id": conversation_id,
                    "userId": other_user_id,
                    "userName": other_user.get("displayName", ""),
                    "userPhoto": other_user.get("photoURL"),
                    "lastMessage": last_message,
                    "lastMessageTime": last_message_time,
                    "isOwnLastMessage": is_own_last_message,
                    "unreadCount": unread_count,
                    "isOnline": other_user.get("isOnline", False),
                    "isArchived": is_archived,
                    "isPinned": is_pinned
                }
                return conversation_response
        
        return None
    except Exception as e:
        print(f"Error getting conversation: {e}")
        return None

async def update_conversation(
    conversation_id: str,
    user_id: str,
    conversation_update: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update a conversation
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID
        conversation_update: Conversation data to update
        
    Returns:
        Updated conversation or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Check if conversation exists and user is part of it
        conversation = await get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        update_data = {"updatedAt": firestore.SERVER_TIMESTAMP}
        
        # Update last read time
        if "lastRead" in conversation_update:
            update_data[f"lastRead.{user_id}"] = firestore.SERVER_TIMESTAMP
            update_data[f"unreadCount.{user_id}"] = 0
        
        # Update archived status
        if "isArchived" in conversation_update:
            update_data[f"isArchived.{user_id}"] = conversation_update["isArchived"]
        
        # Update pinned status
        if "isPinned" in conversation_update:
            update_data[f"isPinned.{user_id}"] = conversation_update["isPinned"]
        
        # Update conversation
        db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).update(update_data)
        
        # Get updated conversation
        updated_conversation = await get_conversation(conversation_id, user_id)
        return updated_conversation
    except Exception as e:
        print(f"Error updating conversation: {e}")
        return None

async def delete_conversation(conversation_id: str, user_id: str) -> bool:
    """
    Delete a conversation
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if conversation exists and user is part of it
        conv_doc = db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).get()
        if not conv_doc.exists:
            return False
            
        conv_data = conv_doc.to_dict()
        
        if user_id not in conv_data.get("userIds", []):
            return False
        
        # Determine the other user in the conversation
        other_user_id = None
        for uid in conv_data.get("userIds", []):
            if uid != user_id:
                other_user_id = uid
                break
        
        # If both users have deleted the conversation, delete it completely
        if conv_data.get("isArchived", {}).get(other_user_id, False):
            # Delete all messages in the conversation
            messages_query = db.collection(MESSAGES_COLLECTION).where("conversationId", "==", conversation_id)
            
            batch = db.batch()
            for msg_doc in messages_query.stream():
                batch.delete(msg_doc.reference)
            
            # Delete conversation
            batch.delete(db.collection(CONVERSATIONS_COLLECTION).document(conversation_id))
            
            # Commit batch
            batch.commit()
        else:
            # Just mark as archived for this user
            db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).update({
                f"isArchived.{user_id}": True,
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
        
        return True
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return False

async def get_messages(
    conversation_id: str,
    user_id: str,
    skip: int = 0,
    limit: int = 50,
    before: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get messages for a conversation
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID
        skip: Number of messages to skip
        limit: Maximum number of messages to return
        before: Get messages before this message ID
        
    Returns:
        List of messages
    """
    db = get_firestore_client()
    
    try:
        # Check if conversation exists and user is part of it
        conversation = await get_conversation(conversation_id, user_id)
        if not conversation:
            return []
        
        # Query messages
        messages_query = db.collection(MESSAGES_COLLECTION).where("conversationId", "==", conversation_id)
        
        # If 'before' is provided, get the message to determine timestamp
        if before:
            before_msg = db.collection(MESSAGES_COLLECTION).document(before).get()
            if before_msg.exists:
                before_time = before_msg.to_dict().get("createdAt")
                messages_query = messages_query.where("createdAt", "<", before_time)
        
        # Order by creation time
        messages_query = messages_query.order_by("createdAt", direction=firestore.Query.DESCENDING).limit(limit).offset(skip)
        
        messages = []
        for msg_doc in messages_query.stream():
            msg_data = msg_doc.to_dict()
            msg_data["id"] = msg_doc.id
            messages.append(msg_data)
        
        # Mark messages as read
        batch = db.batch()
        unread_count = 0
        
        for msg in messages:
            if not msg.get("isRead") and msg.get("senderId") != user_id:
                batch.update(
                    db.collection(MESSAGES_COLLECTION).document(msg["id"]),
                    {"isRead": True, "updatedAt": firestore.SERVER_TIMESTAMP}
                )
                unread_count += 1
        
        # Update conversation if there were unread messages
        if unread_count > 0:
            batch.update(
                db.collection(CONVERSATIONS_COLLECTION).document(conversation_id),
                {
                    f"unreadCount.{user_id}": 0,
                    f"lastRead.{user_id}": firestore.SERVER_TIMESTAMP,
                    "updatedAt": firestore.SERVER_TIMESTAMP
                }
            )
        
        # Commit batch
        batch.commit()
        
        # Return messages in ascending order (oldest first)
        messages.reverse()
        
        return messages
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []

async def send_message(
    conversation_id: str,
    user_id: str,
    message_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Send a new message in a conversation
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID
        message_data: Message data
        
    Returns:
        Created message or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Check if conversation exists and user is part of it
        conv_doc = db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).get()
        if not conv_doc.exists:
            return None
            
        conv_data = conv_doc.to_dict()
        
        if user_id not in conv_data.get("userIds", []):
            return None
        
        # Get user data
        current_user = await get_user_by_uid(user_id)
        if not current_user:
            return None
        
        # Determine the other user in the conversation
        other_user_id = None
        for uid in conv_data.get("userIds", []):
            if uid != user_id:
                other_user_id = uid
                break
        
        # Generate message ID
        message_id = str(uuid.uuid4())
        timestamp = firestore.SERVER_TIMESTAMP
        
        # Create message document
        message = {
            "conversationId": conversation_id,
            "senderId": user_id,
            "senderName": current_user.get("displayName", ""),
            "senderPhoto": current_user.get("photoURL"),
            "content": message_data.get("content"),
            "contentType": message_data.get("contentType", "text"),
            "isRead": False,
            "createdAt": timestamp,
            "updatedAt": timestamp
        }
        
        # Add metadata if provided
        if message_data.get("metadata"):
            message["metadata"] = message_data.get("metadata")
        
        # Create message in Firestore
        db.collection(MESSAGES_COLLECTION).document(message_id).set(message)
        
        # Update conversation
        db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).update({
            "lastMessage": message_data.get("content"),
            "lastMessageTime": timestamp,
            "lastMessageSenderId": user_id,
            f"unreadCount.{other_user_id}": firestore.Increment(1),
            "updatedAt": timestamp,
            # Reset archived status
            f"isArchived.{user_id}": False,
            f"isArchived.{other_user_id}": False
        })
        
        # Create notification for recipient
        notification_id = str(uuid.uuid4())
        
        notification_data = {
            "userId": other_user_id,
            "type": "message_received",
            "sourceUserId": user_id,
            "sourceUserName": current_user.get("displayName", ""),
            "sourceUserPhoto": current_user.get("photoURL"),
            "message": f"New message from {current_user.get('displayName', '')}",
            "data": {
                "conversationId": conversation_id,
                "messageId": message_id
            },
            "isRead": False,
            "createdAt": timestamp
        }
        
        db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification_data)
        
        # Return message with ID
        message_response = message.copy()
        message_response["id"] = message_id
        message_response["createdAt"] = datetime.now()  # Placeholder for SERVER_TIMESTAMP
        message_response["updatedAt"] = datetime.now()  # Placeholder for SERVER_TIMESTAMP
        
        return message_response
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

async def update_message(
    message_id: str,
    user_id: str,
    message_update: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update a message
    
    Args:
        message_id: Message ID
        user_id: User ID
        message_update: Message data to update
        
    Returns:
        Updated message or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Get message
        msg_doc = db.collection(MESSAGES_COLLECTION).document(message_id).get()
        if not msg_doc.exists:
            return None
            
        msg_data = msg_doc.to_dict()
        
        # Check if user is recipient (can only mark as read)
        if msg_data.get("senderId") != user_id and "isRead" in message_update:
            # Only update read status
            db.collection(MESSAGES_COLLECTION).document(message_id).update({
                "isRead": True,
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
            
            # Update conversation unread count
            conversation_id = msg_data.get("conversationId")
            if conversation_id:
                db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).update({
                    f"unreadCount.{user_id}": firestore.Increment(-1),
                    f"lastRead.{user_id}": firestore.SERVER_TIMESTAMP,
                    "updatedAt": firestore.SERVER_TIMESTAMP
                })
            
            # Get updated message
            updated_msg = db.collection(MESSAGES_COLLECTION).document(message_id).get()
            updated_data = updated_msg.to_dict()
            updated_data["id"] = message_id
            
            return updated_data
        
        return None
    except Exception as e:
        print(f"Error updating message: {e}")
        return None

async def upload_message_media(conversation_id: str, file) -> Optional[str]:
    """
    Upload media for a message
    
    Args:
        conversation_id: Conversation ID
        file: Uploaded file
        
    Returns:
        URL of the uploaded media or None if failed
    """
    try:
        # Check if conversation exists
        db = get_firestore_client()
        conv_doc = db.collection(CONVERSATIONS_COLLECTION).document(conversation_id).get()
        if not conv_doc.exists:
            return None
        
        # Create a unique filename
        filename = f"messages/{conversation_id}/{str(uuid.uuid4())}-{file.filename}"
        
        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(filename)
        
        # Read file content
        contents = await file.read()
        
        # Upload to Firebase Storage
        blob.upload_from_string(
            contents,
            content_type=file.content_type
        )
        
        # Make the blob publicly accessible
        blob.make_public()
        
        # Return the public URL
        return blob.public_url
    except Exception as e:
        print(f"Error uploading message media: {e}")
        return None

async def get_or_create_conversation(user_id: str, other_user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get or create a conversation with another user
    
    Args:
        user_id: Current user's ID
        other_user_id: Other user's ID
        
    Returns:
        Conversation data or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Check if users exist
        current_user = await get_user_by_uid(user_id)
        other_user = await get_user_by_uid(other_user_id)
        
        if not current_user or not other_user:
            return None
        
        # Check if conversation already exists
        conversations_query = db.collection(CONVERSATIONS_COLLECTION).where(
            "userIds", "array_contains", user_id
        )
        
        for conv_doc in conversations_query.stream():
            conv_data = conv_doc.to_dict()
            if other_user_id in conv_data.get("userIds", []):
                # Conversation already exists, return it
                return await get_conversation(conv_doc.id, user_id)
        
        # Create new conversation
        return await create_conversation(user_id, other_user_id)
    except Exception as e:
        print(f"Error getting or creating conversation: {e}")
        return None