from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageCreate(BaseModel):
    content: str
    contentType: str = "text"  # text, image, video, audio, location
    metadata: Optional[Dict[str, Any]] = None

class MessageUpdate(BaseModel):
    isRead: Optional[bool] = None

class MessageInDB(BaseModel):
    id: str
    conversationId: str
    senderId: str
    senderName: str
    senderPhoto: Optional[HttpUrl] = None
    content: str
    contentType: str = "text"
    metadata: Optional[Dict[str, Any]] = None
    isRead: bool = False
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        orm_mode = True

class MessageResponse(MessageInDB):
    pass

class MessageList(BaseModel):
    total: int
    messages: List[MessageResponse]
    
    class Config:
        orm_mode = True

class ConversationCreate(BaseModel):
    userId: str
    message: Optional[str] = None

class ConversationUpdate(BaseModel):
    lastRead: Optional[datetime] = None
    isArchived: Optional[bool] = None
    isPinned: Optional[bool] = None

class ConversationInDB(BaseModel):
    id: str
    userIds: List[str]
    lastMessage: Optional[str] = None
    lastMessageTime: Optional[datetime] = None
    lastMessageSenderId: Optional[str] = None
    unreadCount: Dict[str, int] = {}
    createdAt: datetime
    updatedAt: datetime
    isArchived: Dict[str, bool] = {}
    isPinned: Dict[str, bool] = {}
    lastRead: Dict[str, datetime] = {}
    
    class Config:
        orm_mode = True

class ConversationResponse(BaseModel):
    id: str
    userId: str
    userName: str
    userPhoto: Optional[HttpUrl] = None
    lastMessage: Optional[str] = None
    lastMessageTime: Optional[datetime] = None
    isOwnLastMessage: bool = False
    unreadCount: int = 0
    isOnline: bool = False
    isArchived: bool = False
    isPinned: bool = False
    
    class Config:
        orm_mode = True

class ConversationList(BaseModel):
    total: int
    conversations: List[ConversationResponse]
    
    class Config:
        orm_mode = True