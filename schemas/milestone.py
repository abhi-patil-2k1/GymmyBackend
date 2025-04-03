from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AchievementCategory(str, Enum):
    WORKOUT = "workout"
    SOCIAL = "social"
    CONSISTENCY = "consistency"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    FLEXIBILITY = "flexibility"
    NUTRITION = "nutrition"
    WELLNESS = "wellness"
    SPECIAL = "special"

class ChallengeStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class ChallengeProgressUpdate(BaseModel):
    value: int
    notes: Optional[str] = None

class AchievementResponse(BaseModel):
    id: str
    title: str
    description: str
    category: AchievementCategory
    icon: str
    requirements: Dict[str, Any]
    points: int
    isUnlocked: bool
    progress: int
    maxProgress: int
    progressPercentage: float
    unlockedAt: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class AchievementList(BaseModel):
    total: int
    unlocked: int
    achievements: List[AchievementResponse]
    
    class Config:
        orm_mode = True

class ChallengeResponse(BaseModel):
    id: str
    title: str
    description: str
    category: AchievementCategory
    icon: str
    requirements: Dict[str, Any]
    points: int
    status: ChallengeStatus
    progress: int
    maxProgress: int
    progressPercentage: float
    startDate: datetime
    endDate: datetime
    participants: int
    isJoined: bool
    createdBy: Optional[str] = None
    
    class Config:
        orm_mode = True

class ChallengeList(BaseModel):
    total: int
    active: int
    completed: int
    challenges: List[ChallengeResponse]
    
    class Config:
        orm_mode = True

class MilestoneResponse(BaseModel):
    level: int
    totalPoints: int
    pointsForNextLevel: int
    pointsProgress: float
    achievements: List[AchievementResponse]
    challengesActive: List[ChallengeResponse]
    challengesCompleted: List[ChallengeResponse]
    recentActivity: List[Dict[str, Any]]
    
    class Config:
        orm_mode = True

class LeaderboardEntry(BaseModel):
    userId: str
    displayName: str
    photoURL: Optional[HttpUrl] = None
    level: int
    points: int
    achievements: int
    position: int
    
    class Config:
        orm_mode = True

class LeaderboardResponse(BaseModel):
    total: int
    userPosition: int
    leaderboard: List[LeaderboardEntry]
    
    class Config:
        orm_mode = True