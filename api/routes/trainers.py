from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from app.schemas.trainer import (
    TrainerProfileResponse, 
    TrainerUpdate, 
    TrainerList, 
    TrainerStats,
    TrainerAvailabilityResponse,
    TrainerSessionSlot
)
from app.core.security import get_current_user, get_current_active_user, get_current_trainer
from app.services import trainer_service

router = APIRouter(prefix="/api/v1/trainers")

@router.get("/me", response_model=TrainerProfileResponse)
async def get_current_trainer_profile(
    current_user: Dict[str, Any] = Depends(get_current_trainer)
):
    """
    Get current trainer profile
    """
    return current_user

@router.put("/me", response_model=TrainerProfileResponse)
async def update_current_trainer_profile(
    trainer_update: TrainerUpdate,
    current_user: Dict[str, Any] = Depends(get_current_trainer)
):
    """
    Update current trainer profile
    """
    return await trainer_service.update_trainer(current_user["uid"], trainer_update.dict(exclude_unset=True))

@router.get("/me/stats", response_model=TrainerStats)
async def get_current_trainer_stats(
    current_user: Dict[str, Any] = Depends(get_current_trainer)
):
    """
    Get current trainer statistics
    """
    return await trainer_service.get_trainer_stats(current_user["uid"])

@router.get("/me/availability", response_model=TrainerAvailabilityResponse)
async def get_current_trainer_availability(
    current_user: Dict[str, Any] = Depends(get_current_trainer)
):
    """
    Get current trainer's availability slots
    """
    return await trainer_service.get_trainer_availability(current_user["uid"])

@router.post("/me/availability", response_model=TrainerSessionSlot)
async def add_availability_slot(
    slot_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_trainer)
):
    """
    Add new availability slot for current trainer
    """
    return await trainer_service.add_availability_slot(current_user["uid"], slot_data)

@router.delete("/me/availability/{slot_id}")
async def remove_availability_slot(
    slot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_trainer)
):
    """
    Remove availability slot for current trainer
    """
    success = await trainer_service.remove_availability_slot(current_user["uid"], slot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found or cannot be removed"
        )
    return {"message": "Slot removed successfully"}

@router.get("/active", response_model=TrainerList)
async def get_active_trainers(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None
):
    """
    Get all active trainers (trainers who are currently online)
    """
    trainers = await trainer_service.get_active_trainers(skip, limit, search)
    return {
        "total": len(trainers),
        "trainers": trainers
    }

@router.get("/{trainer_id}", response_model=TrainerProfileResponse)
async def get_trainer_profile(
    trainer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific trainer's profile
    """
    trainer = await trainer_service.get_trainer_by_id(trainer_id)
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found"
        )
    return trainer

@router.get("/{trainer_id}/stats", response_model=TrainerStats)
async def get_trainer_stats(
    trainer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific trainer's statistics
    """
    trainer = await trainer_service.get_trainer_by_id(trainer_id)
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found"
        )
    return await trainer_service.get_trainer_stats(trainer_id)

@router.get("/{trainer_id}/availability", response_model=TrainerAvailabilityResponse)
async def get_trainer_availability(
    trainer_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific trainer's availability slots
    """
    trainer = await trainer_service.get_trainer_by_id(trainer_id)
    if not trainer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trainer not found"
        )
    return await trainer_service.get_trainer_availability(trainer_id)

@router.get("/", response_model=TrainerList)
async def list_trainers(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    speciality: Optional[str] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_rate: Optional[float] = None,
    gym_id: Optional[str] = None
):
    """
    List trainers with optional filtering
    """
    filters = {
        "gym_id": gym_id,
        "min_rating": min_rating,
        "max_rate": max_rate
    }
    
    # Parse specialities if provided
    speciality_list = None
    if speciality:
        speciality_list = [s.strip() for s in speciality.split(",")]
    
    trainers = await trainer_service.list_trainers(
        skip=skip, 
        limit=limit, 
        search=search, 
        filters=filters,
        specialities=speciality_list
    )
    
    return {
        "total": len(trainers),
        "trainers": trainers
    }