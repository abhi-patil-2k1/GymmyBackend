from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    CONNECTION_REQUEST = "connection_request"
    CONNECTION_ACCEPTED = "connection_accepted"
    POST_LIKE = "post_like"
    POST_COMMENT = "post_comment"
    COMMENT_LIKE = "comment_like"
    COMMENT_REPLY = "comment_reply"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    CHALLENGE_COMPLETED = "challenge_completed"
    CHALLENGE_INVITATION = "challenge_invitation"
    TRAINER_REQUEST = "trainer_request"
    TRAINING_SESSION_REMINDER = "training_session_reminder"
    GYM_ANNOUNCEMENT = "gym_announcement"
    MESSAGE_RECEIVED = "message_received"
    SYSTEM = "system"

class NotificationUpdate(BaseModel):
    isRead: Optional[bool] = None

class NotificationInDB(BaseModel):
    id: str
    userId: str
    type: NotificationType
    sourceUserId: Optional[str] = None
    sourceUserName: Optional[str] = None
    sourceUserPhoto: Optional[HttpUrl] = None
    message: str
    data: Optional[Dict[str, Any]] = None
    isRead: bool = False
    createdAt: datetime
    
    class Config:
        orm_mode = True

class NotificationResponse(NotificationInDB):
    pass

class NotificationList(BaseModel):
    total: int
    unreadCount: int
    notifications: List[NotificationResponse]
    
    class Config:
        orm_mode = True