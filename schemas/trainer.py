from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.schemas.user import UserStatus, PhysiqueLevel

class TrainerSpeciality(str, Enum):
    WEIGHT_TRAINING = "Weight Training"
    CARDIO = "Cardio"
    CROSSFIT = "CrossFit"
    YOGA = "Yoga"
    PILATES = "Pilates"
    HIIT = "HIIT"
    NUTRITION = "Nutrition"
    REHABILITATION = "Rehabilitation"
    BODYBUILDING = "Bodybuilding"
    POWERLIFTING = "Powerlifting"
    FUNCTIONAL_TRAINING = "Functional Training"
    SPORTS_SPECIFIC = "Sports Specific"
    FLEXIBILITY = "Flexibility"
    SENIOR_FITNESS = "Senior Fitness"
    PRENATAL_FITNESS = "Prenatal Fitness"

class TrainerBase(BaseModel):
    email: Optional[EmailStr] = None
    displayName: Optional[str] = None
    photoURL: Optional[HttpUrl] = None
    
class TrainerCreate(TrainerBase):
    password: str

class TrainerUpdate(TrainerBase):
    bio: Optional[str] = None
    location: Optional[str] = None
    specialities: Optional[List[TrainerSpeciality]] = None
    hourlyRate: Optional[float] = None
    availability: Optional[Dict[str, List[str]]] = None
    certification: Optional[Dict[str, str]] = None
    experience: Optional[int] = None
    gymId: Optional[str] = None
    status: Optional[UserStatus] = None

class TrainerInDB(TrainerBase):
    uid: str
    role: str = "trainer"
    isOnline: bool = False
    status: UserStatus = UserStatus.OFFLINE
    bio: Optional[str] = None
    location: Optional[str] = None
    specialities: List[TrainerSpeciality] = []
    hourlyRate: float = 0.0
    rating: float = 5.0
    totalRatings: int = 0
    totalClients: int = 0
    certifications: Dict[str, str] = {}
    experience: int = 0
    createdAt: datetime
    updatedAt: datetime
    lastActive: Optional[datetime] = None
    gymId: Optional[str] = None
    availability: Dict[str, List[str]] = {}
    
    class Config:
        orm_mode = True

class TrainerResponse(TrainerInDB):
    pass

class TrainerProfileResponse(BaseModel):
    uid: str
    displayName: str
    photoURL: Optional[HttpUrl] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    specialities: List[TrainerSpeciality] = []
    hourlyRate: float
    rating: float
    totalRatings: int
    totalClients: int
    experience: int
    certifications: Dict[str, str] = {}
    status: UserStatus
    isOnline: bool
    
    class Config:
        orm_mode = True

class TrainerList(BaseModel):
    total: int
    trainers: List[TrainerProfileResponse]
    
    class Config:
        orm_mode = True

class TrainerStats(BaseModel):
    clients: int = 0
    sessions: int = 0
    totalHours: float = 0
    ratings: List[Dict[str, Any]] = []
    
    class Config:
        orm_mode = True

class TrainerSessionSlot(BaseModel):
    id: str
    trainerId: str
    date: str
    startTime: str
    endTime: str
    isBooked: bool = False
    clientId: Optional[str] = None
    
    class Config:
        orm_mode = True

class TrainerAvailabilityResponse(BaseModel):
    availableSlots: List[TrainerSessionSlot]
    
    class Config:
        orm_mode = True