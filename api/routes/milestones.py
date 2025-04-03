from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from app.schemas.milestone import (
    AchievementResponse,
    AchievementList,
    ChallengeResponse,
    ChallengeList,
    MilestoneResponse,
    LeaderboardResponse,
    ChallengeProgressUpdate
)
from app.core.security import get_current_user, get_current_active_user
from app.services import milestone_service

router = APIRouter(prefix="/api/v1/milestones")

@router.get("/", response_model=MilestoneResponse)
async def get_user_milestones(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get user's milestone data (level, achievements, challenges)
    """
    milestones = await milestone_service.get_user_milestones(current_user["uid"])
    return milestones

@router.get("/achievements", response_model=AchievementList)
async def get_achievements(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    category: Optional[str] = None,
    unlocked_only: bool = False
):
    """
    Get all achievements with user's progress
    """
    achievements = await milestone_service.get_achievements(
        current_user["uid"],
        category=category,
        unlocked_only=unlocked_only
    )
    
    return {
        "total": len(achievements),
        "unlocked": sum(1 for a in achievements if a.get("isUnlocked", False)),
        "achievements": achievements
    }

@router.get("/achievements/{achievement_id}", response_model=AchievementResponse)
async def get_achievement(
    achievement_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific achievement with user's progress
    """
    achievement = await milestone_service.get_achievement(achievement_id, current_user["uid"])
    if not achievement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Achievement not found"
        )
    return achievement

@router.get("/challenges", response_model=ChallengeList)
async def get_challenges(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    category: Optional[str] = None,
    status: Optional[str] = None,
    joined_only: bool = False
):
    """
    Get available challenges with user's progress
    """
    challenges = await milestone_service.get_challenges(
        current_user["uid"],
        category=category,
        status=status,
        joined_only=joined_only
    )
    
    active_count = sum(1 for c in challenges if c.get("status") == "active" and c.get("isJoined", False))
    completed_count = sum(1 for c in challenges if c.get("status") == "completed" and c.get("isJoined", False))
    
    return {
        "total": len(challenges),
        "active": active_count,
        "completed": completed_count,
        "challenges": challenges
    }

@router.get("/challenges/{challenge_id}", response_model=ChallengeResponse)
async def get_challenge(
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific challenge with user's progress
    """
    challenge = await milestone_service.get_challenge(challenge_id, current_user["uid"])
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )
    return challenge

@router.post("/challenges/{challenge_id}/join")
async def join_challenge(
    challenge_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Join a challenge
    """
    success = await milestone_service.join_challenge(challenge_id, current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to join challenge"
        )
    return {"message": "Successfully joined challenge"}

@router.put("/challenges/{challenge_id}/progress")
async def update_challenge_progress(
    challenge_id: str,
    progress_update: ChallengeProgressUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update progress for a challenge
    """
    updated_challenge = await milestone_service.update_challenge_progress(
        challenge_id,
        current_user["uid"],
        progress_update.value,
        progress_update.notes
    )
    
    if not updated_challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update challenge progress"
        )
    
    return updated_challenge

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    time_period: Optional[str] = "all"  # all, week, month
):
    """
    Get leaderboard of users by points/level
    """
    leaderboard, user_position = await milestone_service.get_leaderboard(
        current_user["uid"],
        skip=skip,
        limit=limit,
        time_period=time_period
    )
    
    return {
        "total": len(leaderboard),
        "userPosition": user_position,
        "leaderboard": leaderboard
    }

@router.get("/user/{user_id}", response_model=MilestoneResponse)
async def get_user_milestones_by_id(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get another user's milestone data
    """
    milestones = await milestone_service.get_user_milestones(user_id)
    if not milestones:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return milestones