from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.schemas.user import UserStatus

class GymFacility(str, Enum):
    CARDIO_EQUIPMENT = "Cardio Equipment"
    STRENGTH_EQUIPMENT = "Strength Equipment"
    POOL = "Pool"
    SAUNA = "Sauna"
    BASKETBALL_COURT = "Basketball Court"
    YOGA_STUDIO = "Yoga Studio"
    GROUP_CLASSES = "Group Classes"
    PERSONAL_TRAINING = "Personal Training"
    LOCKER_ROOMS = "Locker Rooms"
    SHOWER = "Shower"
    JUICE_BAR = "Juice Bar"
    CHILDCARE = "Childcare"
    PARKING = "Parking"
    WIFI = "WiFi"
    FITNESS_ASSESSMENT = "Fitness Assessment"

class GymAdminBase(BaseModel):
    email: Optional[EmailStr] = None
    displayName: Optional[str] = None
    photoURL: Optional[HttpUrl] = None
    
class GymAdminCreate(GymAdminBase):
    password: str

class GymAdminUpdate(GymAdminBase):
    gymName: Optional[str] = None
    gymLocation: Optional[str] = None
    gymDescription: Optional[str] = None
    gymFacilities: Optional[List[GymFacility]] = None
    gymHours: Optional[Dict[str, Dict[str, str]]] = None
    gymContactEmail: Optional[EmailStr] = None
    gymContactPhone: Optional[str] = None
    gymPhotos: Optional[List[HttpUrl]] = None
    status: Optional[UserStatus] = None

class GymAdminInDB(GymAdminBase):
    uid: str
    role: str = "gym_admin"
    isOnline: bool = False
    status: UserStatus = UserStatus.OFFLINE
    gymId: str
    gymName: str
    gymLocation: str
    gymDescription: Optional[str] = None
    gymFacilities: List[GymFacility] = []
    gymHours: Dict[str, Dict[str, str]] = {}
    gymContactEmail: Optional[EmailStr] = None
    gymContactPhone: Optional[str] = None
    gymPhotos: List[HttpUrl] = []
    memberCount: int = 0
    trainerCount: int = 0
    createdAt: datetime
    updatedAt: datetime
    lastActive: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class GymAdminResponse(GymAdminInDB):
    pass

class GymProfileResponse(BaseModel):
    gymId: str
    adminUid: str
    gymName: str
    gymLocation: str
    gymDescription: Optional[str] = None
    gymFacilities: List[GymFacility] = []
    gymHours: Dict[str, Dict[str, str]] = {}
    gymContactEmail: Optional[EmailStr] = None
    gymContactPhone: Optional[str] = None
    gymPhotos: List[HttpUrl] = []
    memberCount: int = 0
    trainerCount: int = 0
    
    class Config:
        orm_mode = True

class GymList(BaseModel):
    total: int
    gyms: List[GymProfileResponse]
    
    class Config:
        orm_mode = True

class GymStats(BaseModel):
    memberCount: int = 0
    activeMembers: int = 0
    trainerCount: int = 0
    totalCheckins: int = 0
    popularHours: Dict[str, int] = {}
    popularFacilities: Dict[str, int] = {}
    
    class Config:
        orm_mode = True

class GymMemberResponse(BaseModel):
    uid: str
    displayName: str
    photoURL: Optional[HttpUrl] = None
    joinDate: datetime
    lastCheckin: Optional[datetime] = None
    membershipType: str
    membershipExpiration: Optional[datetime] = None
    checkinCount: int = 0
    
    class Config:
        orm_mode = True

class GymMemberList(BaseModel):
    total: int
    members: List[GymMemberResponse]
    
    class Config:
        orm_mode = True

class GymTrainerResponse(BaseModel):
    uid: str
    displayName: str
    photoURL: Optional[HttpUrl] = None
    joinDate: datetime
    specialities: List[str] = []
    clientCount: int = 0
    sessionCount: int = 0
    
    class Config:
        orm_mode = True

class GymTrainerList(BaseModel):
    total: int
    trainers: List[GymTrainerResponse]
    
    class Config:
        orm_mode = True