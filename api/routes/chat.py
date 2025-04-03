from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from typing import Dict, List, Any, Optional
from app.schemas.chat import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageList,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationList 
)
from app.core.security import get_current_user, get_current_active_user
from app.services import chat_service

router = APIRouter(prefix="/api/v1/chat")

@router.get("/conversations", response_model=ConversationList)
async def get_conversations(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    archived: bool = False
):
    """
    Get user's conversations
    """
    conversations = await chat_service.get_conversations(
        current_user["uid"],
        skip=skip,
        limit=limit,
        archived=archived
    )
    return {
        "total": len(conversations),
        "conversations": conversations
    }

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new conversation with another user
    """
    if conversation_data.userId == current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create conversation with yourself"
        )
    
    conversation = await chat_service.create_conversation(
        current_user["uid"],
        conversation_data.userId,
        conversation_data.message
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create conversation"
        )
    
    return conversation

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific conversation
    """
    conversation = await chat_service.get_conversation(conversation_id, current_user["uid"])
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation

@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update a conversation (mark as read, archive, pin)
    """
    conversation = await chat_service.update_conversation(
        conversation_id,
        current_user["uid"],
        conversation_update.dict(exclude_unset=True)
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update conversation"
        )
    
    return conversation

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a conversation
    """
    success = await chat_service.delete_conversation(conversation_id, current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete conversation"
        )
    return {"message": "Conversation deleted successfully"}

@router.get("/conversations/{conversation_id}/messages", response_model=MessageList)
async def get_conversation_messages(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    before: Optional[str] = None
):
    """
    Get messages for a conversation
    """
    conversation = await chat_service.get_conversation(conversation_id, current_user["uid"])
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = await chat_service.get_messages(
        conversation_id,
        current_user["uid"],
        skip=skip,
        limit=limit,
        before=before
    )
    
    return {
        "total": len(messages),
        "messages": messages
    }

@router.post("/messages", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Send a new message in a conversation
    """
    # Check if conversation exists and user is part of it
    conversation = await chat_service.get_conversation(conversation_id, current_user["uid"])
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    message = await chat_service.send_message(
        conversation_id,
        current_user["uid"],
        message_data
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send message"
        )
    
    return message

@router.put("/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: str,
    message_update: MessageUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update a message (mark as read)
    """
    message = await chat_service.update_message(
        message_id,
        current_user["uid"],
        message_update.dict(exclude_unset=True)
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update message"
        )
    
    return message

@router.post("/messages/media")
async def upload_message_media(
    conversation_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Upload media for a message
    """
    # Check if conversation exists and user is part of it
    conversation = await chat_service.get_conversation(conversation_id, current_user["uid"])
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    media_url = await chat_service.upload_message_media(conversation_id, file)
    if not media_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload media"
        )
    
    return {"mediaUrl": media_url}

@router.get("/users/{user_id}/conversation")
async def get_conversation_with_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get or create a conversation with a specific user
    """
    if user_id == current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create conversation with yourself"
        )
    
    conversation = await chat_service.get_or_create_conversation(
        current_user["uid"],
        user_id
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get or create conversation"
        )
    
    return {"conversationId": conversation.get("id")}