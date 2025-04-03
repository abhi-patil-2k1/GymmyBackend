from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import Dict, Any
from app.core.security import get_current_user, get_current_active_user
from app.schemas.user import UserCreate, UserResponse
from app.schemas.trainer import TrainerCreate
from app.schemas.gym_admin import GymAdminCreate
from app.db.firebase_client import update_user_status
from app.services import user_service, trainer_service, gym_admin_service

router = APIRouter(prefix="/api/v1/auth")

@router.post("/verify-token", response_model=UserResponse)
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Verify Firebase ID token and return user data
    """
    return current_user

@router.post("/register/user", response_model=Dict[str, str])
async def register_user(
    user_data: UserCreate = Body(...)
):
    """
    Register a new regular user
    """
    uid = await user_service.create_user(user_data.dict())
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register user"
        )
    return {"uid": uid, "message": "User registered successfully"}

@router.post("/register/trainer", response_model=Dict[str, str])
async def register_trainer(
    trainer_data: TrainerCreate = Body(...)
):
    """
    Register a new trainer
    """
    uid = await trainer_service.create_trainer(trainer_data.dict())
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register trainer"
        )
    return {"uid": uid, "message": "Trainer registered successfully"}

@router.post("/register/gym-admin", response_model=Dict[str, str])
async def register_gym_admin(
    gym_admin_data: GymAdminCreate = Body(...)
):
    """
    Register a new gym admin
    """
    uid = await gym_admin_service.create_gym_admin(gym_admin_data.dict())
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register gym admin"
        )
    return {"uid": uid, "message": "Gym admin registered successfully"}

@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Logout user and update online status
    """
    success = await update_user_status(current_user["uid"], False)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )
    return {"message": "Logged out successfully"}