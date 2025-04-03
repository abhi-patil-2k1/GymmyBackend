from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ConnectionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"

class ConnectionRequest(BaseModel):
    message: Optional[str] = None

class ConnectionAction(BaseModel):
    action: str  # accept, reject, block

class ConnectionInDB(BaseModel):
    id: str
    userIds: List[str]
    requesterId: str
    recipientId: str
    status: ConnectionStatus
    message: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        orm_mode = True

class ConnectionResponse(BaseModel):
    id: str
    userId: str
    status: ConnectionStatus
    displayName: str
    photoURL: Optional[HttpUrl] = None
    isRequester: bool
    message: Optional[str] = None
    createdAt: datetime
    
    class Config:
        orm_mode = True

class ConnectionList(BaseModel):
    total: int
    connections: List[ConnectionResponse]
    
    class Config:
        orm_mode = True