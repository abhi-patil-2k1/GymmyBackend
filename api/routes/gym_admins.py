from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from typing import Dict, List, Any, Optional
from app.schemas.gym_admin import (
    GymAdminResponse, 
    GymAdminUpdate, 
    GymList, 
    GymStats,
    GymProfileResponse,
    GymMemberList,
    GymTrainerList
)
from app.core.security import get_current_user, get_current_active_user, get_current_gym_admin
from app.services import gym_admin_service

router = APIRouter(prefix="/api/v1/gyms")

@router.get("/me", response_model=GymAdminResponse)
async def get_current_gym_admin_profile(
    current_user: Dict[str, Any] = Depends(get_current_gym_admin)
):
    """
    Get current gym admin profile
    """
    return current_user

@router.put("/me", response_model=GymAdminResponse)
async def update_current_gym_admin_profile(
    gym_update: GymAdminUpdate,
    current_user: Dict[str, Any] = Depends(get_current_gym_admin)
):
    """
    Update current gym admin profile
    """
    return await gym_admin_service.update_gym_admin(current_user["uid"], gym_update.dict(exclude_unset=True))

@router.post("/me/photos")
async def upload_gym_photo(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_gym_admin)
):
    """
    Upload a photo for the gym
    """
    photo_url = await gym_admin_service.upload_gym_photo(current_user["uid"], file)
    if not photo_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload photo"
        )
    return {"photoUrl": photo_url}

@router.get("/me/stats", response_model=GymStats)
async def get_current_gym_stats(
    current_user: Dict[str, Any] = Depends(get_current_gym_admin)
):
    """
    Get current gym statistics
    """
    return await gym_admin_service.get_gym_stats(current_user["gymId"])

@router.get("/me/members", response_model=GymMemberList)
async def get_current_gym_members(
    current_user: Dict[str, Any] = Depends(get_current_gym_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    membership_type: Optional[str] = None,
    active_only: bool = False
):
    """
    Get members of the current gym
    """
    members = await gym_admin_service.get_gym_members(
        current_user["gymId"],
        skip=skip,
        limit=limit,
        search=search,
        membership_type=membership_type,
        active_only=active_only
    )
    return {
        "total": len(members),
        "members": members
    }

@router.get("/me/trainers", response_model=GymTrainerList)
async def get_current_gym_trainers(
    current_user: Dict[str, Any] = Depends(get_current_gym_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    speciality: Optional[str] = None
):
    """
    Get trainers of the current gym
    """
    trainers = await gym_admin_service.get_gym_trainers(
        current_user["gymId"],
        skip=skip,
        limit=limit,
        search=search,
        speciality=speciality
    )
    return {
        "total": len(trainers),
        "trainers": trainers
    }

@router.post("/me/members/{user_id}")
async def add_member_to_gym(
    user_id: str,
    membership_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_gym_admin)
):
    """
    Add a user as a member to the current gym
    """
    success = await gym_admin_service.add_member_to_gym(
        current_user["gymId"],
        user_id,
        membership_data
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add member to gym"
        )
    return {"message": "Member added successfully"}

@router.post("/me/trainers/{trainer_id}")
async def add_trainer_to_gym(
    trainer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_gym_admin)
):
    """
    Add a trainer to the current gym
    """
    success = await gym_admin_service.add_trainer_to_gym(
        current_user["gymId"],
        trainer_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add trainer to gym"
        )
    return {"message": "Trainer added successfully"}

@router.delete("/me/members/{user_id}")
async def remove_member_from_gym(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_gym_admin)
):
    """
    Remove a member from the current gym
    """
    success = await gym_admin_service.remove_member_from_gym(
        current_user["gymId"],
        user_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove member from gym"
        )
    return {"message": "Member removed successfully"}

@router.delete("/me/trainers/{trainer_id}")
async def remove_trainer_from_gym(
    trainer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_gym_admin)
):
    """
    Remove a trainer from the current gym
    """
    success = await gym_admin_service.remove_trainer_from_gym(
        current_user["gymId"],
        trainer_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove trainer from gym"
        )
    return {"message": "Trainer removed successfully"}

@router.get("/{gym_id}", response_model=GymProfileResponse)
async def get_gym_profile(
    gym_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific gym's profile
    """
    gym = await gym_admin_service.get_gym_by_id(gym_id)
    if not gym:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gym not found"
        )
    return gym

@router.get("/", response_model=GymList)
async def list_gyms(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    facilities: Optional[str] = None,
    location: Optional[str] = None
):
    """
    List gyms with optional filtering
    """
    filters = {
        "location": location
    }
    
    # Parse facilities if provided
    facility_list = None
    if facilities:
        facility_list = [f.strip() for f in facilities.split(",")]
    
    gyms = await gym_admin_service.list_gyms(
        skip=skip, 
        limit=limit, 
        search=search, 
        filters=filters,
        facilities=facility_list
    )
    
    return {
        "total": len(gyms),
        "gyms": gyms
    }