from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    TRAINER = "trainer"
    GYM_ADMIN = "gym_admin"

class UserStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class PhysiqueLevel(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    displayName: Optional[str] = None
    photoURL: Optional[HttpUrl] = None
    
class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.USER

class UserUpdate(UserBase):
    bio: Optional[str] = None
    location: Optional[str] = None
    physique: Optional[PhysiqueLevel] = None
    interests: Optional[List[str]] = None
    availability: Optional[Dict[str, List[str]]] = None
    gymId: Optional[str] = None
    status: Optional[UserStatus] = None

class UserInDB(UserBase):
    uid: str
    role: UserRole = UserRole.USER
    isOnline: bool = False
    status: UserStatus = UserStatus.OFFLINE
    bio: Optional[str] = None
    location: Optional[str] = None
    physique: Optional[PhysiqueLevel] = None
    interests: List[str] = []
    rating: float = 5.0
    totalRatings: int = 0
    achievements: List[str] = []
    level: int = 1
    experiencePoints: int = 0
    createdAt: datetime
    updatedAt: datetime
    lastActive: Optional[datetime] = None
    gymId: Optional[str] = None
    availability: Dict[str, List[str]] = {}
    social: Dict[str, Any] = {}
    
    class Config:
        orm_mode = True

class UserResponse(UserInDB):
    pass

class UserProfileResponse(BaseModel):
    uid: str
    displayName: str
    photoURL: Optional[HttpUrl] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    physique: Optional[PhysiqueLevel] = None
    interests: List[str] = []
    rating: float = 5.0
    status: UserStatus
    isOnline: bool
    role: UserRole
    level: int
    achievements: List[str] = []
    
    class Config:
        orm_mode = True

class UserList(BaseModel):
    total: int
    users: List[UserProfileResponse]
    
    class Config:
        orm_mode = True

class UserStats(BaseModel):
    posts: int = 0
    connections: int = 0
    workouts: int = 0
    level: int = 1
    achievements: int = 0
    
    class Config:
        orm_mode = True