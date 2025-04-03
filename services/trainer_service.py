from typing import Dict, List, Any, Optional
from app.db.firebase_client import get_user_by_uid
from app.config.firebase import get_firestore_client
from firebase_admin import firestore
import uuid
from datetime import datetime

# Collection names
TRAINERS_COLLECTION = "trainers"
TRAINER_SLOTS_COLLECTION = "trainerSlots"
TRAINER_SESSIONS_COLLECTION = "trainerSessions"
TRAINER_RATINGS_COLLECTION = "trainerRatings"

async def get_trainer_by_id(trainer_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a trainer by ID
    
    Args:
        trainer_id: Trainer ID
        
    Returns:
        Trainer data or None if not found
    """
    trainer = await get_user_by_uid(trainer_id)
    if trainer and trainer.get("role") == "trainer":
        return trainer
    return None

async def update_trainer(trainer_id: str, trainer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a trainer's profile
    
    Args:
        trainer_id: Trainer ID
        trainer_data: Trainer data to update
        
    Returns:
        Updated trainer data or None if failed
    """
    db = get_firestore_client()
    try:
        # First check if the trainer exists
        trainer = await get_trainer_by_id(trainer_id)
        if not trainer:
            return None
        
        # Add updated timestamp
        trainer_data["updatedAt"] = firestore.SERVER_TIMESTAMP
        
        # Update trainer document
        db.collection(TRAINERS_COLLECTION).document(trainer_id).update(trainer_data)
        
        # Get updated trainer
        updated_trainer = await get_trainer_by_id(trainer_id)
        return updated_trainer
    except Exception as e:
        print(f"Error updating trainer: {e}")
        return None

async def get_active_trainers(skip: int = 0, limit: int = 20, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all active trainers
    
    Args:
        skip: Number of trainers to skip
        limit: Maximum number of trainers to return
        search: Optional search query
        
    Returns:
        List of active trainers
    """
    db = get_firestore_client()
    
    # Get active trainers
    query = db.collection(TRAINERS_COLLECTION).where("isOnline", "==", True)
    results = query.stream()
    
    active_trainers = []
    for doc in results:
        trainer_data = doc.to_dict()
        trainer_data["uid"] = doc.id
        active_trainers.append(trainer_data)
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        active_trainers = [
            trainer for trainer in active_trainers
            if search_lower in trainer.get("displayName", "").lower() or
            search_lower in trainer.get("email", "").lower() or
            any(search_lower in speciality.lower() for speciality in trainer.get("specialities", []))
        ]
    
    # Apply pagination
    paginated_trainers = active_trainers[skip:skip + limit]
    
    return paginated_trainers

async def list_trainers(
    skip: int = 0, 
    limit: int = 20, 
    search: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    specialities: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    List trainers with optional filtering
    
    Args:
        skip: Number of trainers to skip
        limit: Maximum number of trainers to return
        search: Optional search query
        filters: Optional filters
        specialities: Optional list of specialities to filter by
        
    Returns:
        List of trainers
    """
    db = get_firestore_client()
    
    # Start with base query
    query = db.collection(TRAINERS_COLLECTION)
    
    # Apply gym_id filter if provided
    if filters and filters.get("gym_id"):
        query = query.where("gymId", "==", filters["gym_id"])
    
    # Execute query
    results = query.stream()
    trainers = []
    
    for doc in results:
        trainer_data = doc.to_dict()
        trainer_data["uid"] = doc.id
        
        # Apply min_rating filter
        if filters and filters.get("min_rating") is not None:
            if trainer_data.get("rating", 0) < filters["min_rating"]:
                continue
        
        # Apply max_rate filter
        if filters and filters.get("max_rate") is not None:
            if trainer_data.get("hourlyRate", 0) > filters["max_rate"]:
                continue
        
        trainers.append(trainer_data)
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        trainers = [
            trainer for trainer in trainers
            if search_lower in trainer.get("displayName", "").lower() or
            search_lower in trainer.get("email", "").lower() or
            any(search_lower in speciality.lower() for speciality in trainer.get("specialities", []))
        ]
    
    # Apply specialities filter if provided
    if specialities:
        trainers = [
            trainer for trainer in trainers
            if any(speciality in trainer.get("specialities", []) for speciality in specialities)
        ]
    
    # Sort by online status first, then by rating
    trainers.sort(key=lambda x: (not x.get("isOnline", False), -x.get("rating", 0)))
    
    # Apply pagination
    paginated_trainers = trainers[skip:skip + limit]
    
    return paginated_trainers

async def get_trainer_stats(trainer_id: str) -> Dict[str, Any]:
    """
    Get a trainer's statistics
    
    Args:
        trainer_id: Trainer ID
        
    Returns:
        Trainer statistics
    """
    db = get_firestore_client()
    
    # Get client count (unique users who booked sessions)
    sessions_ref = db.collection(TRAINER_SESSIONS_COLLECTION).where("trainerId", "==", trainer_id)
    sessions = list(sessions_ref.stream())
    clients = set(session.to_dict().get("clientId") for session in sessions if session.to_dict().get("clientId"))
    client_count = len(clients)
    
    # Get session count
    session_count = len(sessions)
    
    # Calculate total hours
    total_hours = 0
    for session in sessions:
        session_data = session.to_dict()
        if session_data.get("durationMinutes"):
            total_hours += session_data.get("durationMinutes") / 60
    
    # Get ratings
    ratings_ref = db.collection(TRAINER_RATINGS_COLLECTION).where("trainerId", "==", trainer_id).limit(10)
    ratings = []
    for rating_doc in ratings_ref.stream():
        rating_data = rating_doc.to_dict()
        rating_data["id"] = rating_doc.id
        ratings.append(rating_data)
    
    return {
        "clients": client_count,
        "sessions": session_count,
        "totalHours": total_hours,
        "ratings": ratings
    }

async def get_trainer_availability(trainer_id: str) -> Dict[str, Any]:
    """
    Get a trainer's availability slots
    
    Args:
        trainer_id: Trainer ID
        
    Returns:
        Trainer availability slots
    """
    db = get_firestore_client()
    
    # Get availability slots
    slots_ref = db.collection(TRAINER_SLOTS_COLLECTION).where("trainerId", "==", trainer_id)
    
    # Only get future slots (greater than current date)
    current_date = datetime.now().strftime("%Y-%m-%d")
    slots_ref = slots_ref.where("date", ">=", current_date)
    
    available_slots = []
    for slot_doc in slots_ref.stream():
        slot_data = slot_doc.to_dict()
        slot_data["id"] = slot_doc.id
        available_slots.append(slot_data)
    
    # Sort by date and time
    available_slots.sort(key=lambda x: (x.get("date", ""), x.get("startTime", "")))
    
    return {"availableSlots": available_slots}

async def add_availability_slot(trainer_id: str, slot_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add new availability slot for a trainer
    
    Args:
        trainer_id: Trainer ID
        slot_data: Slot data to add
        
    Returns:
        Created slot data
    """
    db = get_firestore_client()
    
    # Generate unique ID for slot
    slot_id = str(uuid.uuid4())
    
    # Add trainer ID and create timestamp
    slot_data["trainerId"] = trainer_id
    slot_data["createdAt"] = firestore.SERVER_TIMESTAMP
    slot_data["isBooked"] = False
    
    # Create slot document
    db.collection(TRAINER_SLOTS_COLLECTION).document(slot_id).set(slot_data)
    
   # Get created slot
    created_slot = db.collection(TRAINER_SLOTS_COLLECTION).document(slot_id).get()
    
    # Return slot data with ID
    slot_response = created_slot.to_dict()
    slot_response["id"] = slot_id
    
    return slot_response

async def remove_availability_slot(trainer_id: str, slot_id: str) -> bool:
    """
    Remove availability slot for a trainer
    
    Args:
        trainer_id: Trainer ID
        slot_id: Slot ID to remove
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Get slot to verify it belongs to the trainer and is not booked
        slot_doc = db.collection(TRAINER_SLOTS_COLLECTION).document(slot_id).get()
        
        if not slot_doc.exists:
            return False
            
        slot_data = slot_doc.to_dict()
        
        # Verify slot belongs to the trainer
        if slot_data.get("trainerId") != trainer_id:
            return False
            
        # Verify slot is not booked
        if slot_data.get("isBooked", False):
            return False
            
        # Delete slot
        db.collection(TRAINER_SLOTS_COLLECTION).document(slot_id).delete()
        
        return True
    except Exception as e:
        print(f"Error removing slot: {e}")
        return False