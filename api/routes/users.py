from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from app.schemas.user import UserProfileResponse, UserUpdate, UserList, UserStats
from app.core.security import get_current_user, get_current_active_user
from app.services import user_service

router = APIRouter(prefix="/api/v1/users")

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get current user profile
    """
    return current_user

@router.put("/me", response_model=UserProfileResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update current user profile
    """
    return await user_service.update_user(current_user["uid"], user_update.dict(exclude_unset=True))

@router.get("/me/stats", response_model=UserStats)
async def get_current_user_stats(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get current user statistics
    """
    return await user_service.get_user_stats(current_user["uid"])

@router.get("/active", response_model=UserList)
async def get_active_users(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
):
    """
    Get all active users (users who are currently online)
    """
    users = await user_service.get_active_users(skip, limit, search)
    return {
        "total": len(users),
        "users": users
    }

@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific user's profile
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific user's statistics
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return await user_service.get_user_stats(user_id)

@router.get("/", response_model=UserList)
async def list_users(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    physique: Optional[str] = None,
    interests: Optional[str] = None,
    gym_id: Optional[str] = None
):
    """
    List users with optional filtering
    """
    filters = {
        "status": status,
        "physique": physique,
        "gym_id": gym_id
    }
    
    # Parse interests if provided
    interest_list = None
    if interests:
        interest_list = [i.strip() for i in interests.split(",")]
    
    users = await user_service.list_users(
        skip=skip, 
        limit=limit, 
        search=search, 
        filters=filters,
        interests=interest_list
    )
    
    return {
        "total": len(users),
        "users": users
    }