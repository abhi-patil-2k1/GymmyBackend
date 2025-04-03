from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PostPrivacy(str, Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    GYM = "gym"
    PRIVATE = "private"

class PostType(str, Enum):
    UPDATE = "update"
    EVENT = "event"
    POLL = "poll"
    ACHIEVEMENT = "achievement"
    WORKOUT = "workout"

class PostBase(BaseModel):
    content: str
    privacy: PostPrivacy = PostPrivacy.PUBLIC
    postType: PostType = PostType.UPDATE
    media: List[HttpUrl] = []
    tags: List[str] = []
    location: Optional[str] = None

class PostCreate(PostBase):
    gymId: Optional[str] = None
    eventData: Optional[Dict[str, Any]] = None
    pollData: Optional[Dict[str, Any]] = None
    workoutData: Optional[Dict[str, Any]] = None
    achievementData: Optional[Dict[str, Any]] = None

class PostUpdate(BaseModel):
    content: Optional[str] = None
    privacy: Optional[PostPrivacy] = None
    media: Optional[List[HttpUrl]] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None

class PostInDB(PostBase):
    id: str
    userId: str
    userName: str
    userPhoto: Optional[HttpUrl] = None
    gymId: Optional[str] = None
    eventData: Optional[Dict[str, Any]] = None
    pollData: Optional[Dict[str, Any]] = None
    workoutData: Optional[Dict[str, Any]] = None
    achievementData: Optional[Dict[str, Any]] = None
    likeCount: int = 0
    commentCount: int = 0
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        orm_mode = True

class PostResponse(PostInDB):
    liked: bool = False
    
    class Config:
        orm_mode = True

class PostList(BaseModel):
    total: int
    posts: List[PostResponse]
    
    class Config:
        orm_mode = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentUpdate(BaseModel):
    content: Optional[str] = None

class CommentInDB(CommentBase):
    id: str
    postId: str
    userId: str
    userName: str
    userPhoto: Optional[HttpUrl] = None
    likeCount: int = 0
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        orm_mode = True

class CommentResponse(CommentInDB):
    liked: bool = False
    
    class Config:
        orm_mode = True

class CommentList(BaseModel):
    total: int
    comments: List[CommentResponse]
    
    class Config:
        orm_mode = True