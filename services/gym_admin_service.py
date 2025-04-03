from typing import Dict, List, Any, Optional
from app.db.firebase_client import get_user_by_uid
from app.config.firebase import get_firestore_client, get_auth_client
from firebase_admin import firestore, storage, auth
import uuid
from datetime import datetime
import os

# Collection names
GYM_ADMIN_COLLECTION = "gymAdmins"
GYMS_COLLECTION = "gyms"
GYM_MEMBERS_COLLECTION = "gymMembers"
USERS_COLLECTION = "users"
TRAINERS_COLLECTION = "trainers"
CHECKINS_COLLECTION = "checkins"

async def get_gym_by_id(gym_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a gym by ID
    
    Args:
        gym_id: Gym ID
        
    Returns:
        Gym data or None if not found
    """
    db = get_firestore_client()
    
    # Get gym from Firestore
    gym_doc = db.collection(GYMS_COLLECTION).document(gym_id).get()
    if not gym_doc.exists:
        return None
        
    gym_data = gym_doc.to_dict()
    gym_data["gymId"] = gym_id
    
    # Get admin data
    admin_uid = gym_data.get("adminUid")
    if admin_uid:
        admin = await get_user_by_uid(admin_uid)
        if admin:
            gym_data["adminName"] = admin.get("displayName")
    
    return gym_data

async def get_gym_by_admin_id(admin_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a gym by admin ID
    
    Args:
        admin_id: Admin user ID
        
    Returns:
        Gym data or None if not found
    """
    db = get_firestore_client()
    
    # Query gyms with the given admin ID
    gyms_ref = db.collection(GYMS_COLLECTION).where("adminUid", "==", admin_id).limit(1)
    gyms = list(gyms_ref.stream())
    
    if not gyms:
        return None
        
    gym_doc = gyms[0]
    gym_data = gym_doc.to_dict()
    gym_data["gymId"] = gym_doc.id
    
    return gym_data

async def create_gym_admin(admin_data: Dict[str, Any]) -> Optional[str]:
    """
    Create a new gym admin and gym
    
    Args:
        admin_data: Admin data to create
        
    Returns:
        Admin user ID if successful, None otherwise
    """
    db = get_firestore_client()
    auth_client = get_auth_client()
    
    try:
        # Create user in Firebase Auth
        user_record = auth_client.create_user(
            email=admin_data.get("email"),
            password=admin_data.get("password"),
            display_name=admin_data.get("displayName"),
            photo_url=admin_data.get("photoURL"),
        )
        
        # Get UID
        uid = user_record.uid
        
        # Create gym document
        gym_id = str(uuid.uuid4())
        gym_name = admin_data.get("gymName", f"Gym {gym_id[:8]}")
        
        gym_data = {
            "adminUid": uid,
            "gymName": gym_name,
            "gymLocation": admin_data.get("gymLocation", ""),
            "gymDescription": admin_data.get("gymDescription", ""),
            "gymFacilities": admin_data.get("gymFacilities", []),
            "gymHours": admin_data.get("gymHours", {}),
            "gymContactEmail": admin_data.get("email"),
            "gymContactPhone": admin_data.get("gymContactPhone", ""),
            "gymPhotos": admin_data.get("gymPhotos", []),
            "memberCount": 0,
            "trainerCount": 0,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        
        # Create gym in Firestore
        db.collection(GYMS_COLLECTION).document(gym_id).set(gym_data)
        
        # Create admin user in Firestore
        admin_doc = {
            "uid": uid,
            "email": admin_data.get("email"),
            "displayName": admin_data.get("displayName"),
            "photoURL": admin_data.get("photoURL"),
            "role": "gym_admin",
            "gymId": gym_id,
            "isOnline": True,
            "status": "available",
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP,
            "lastActive": firestore.SERVER_TIMESTAMP,
            "gymName": gym_name,
            "gymLocation": admin_data.get("gymLocation", ""),
            "gymDescription": admin_data.get("gymDescription", ""),
            "gymFacilities": admin_data.get("gymFacilities", []),
            "gymHours": admin_data.get("gymHours", {}),
            "gymContactEmail": admin_data.get("email"),
            "gymContactPhone": admin_data.get("gymContactPhone", ""),
            "gymPhotos": admin_data.get("gymPhotos", []),
            "memberCount": 0,
            "trainerCount": 0,
        }
        
        db.collection(GYM_ADMIN_COLLECTION).document(uid).set(admin_doc)
        
        # Set custom claims to identify user as gym admin
        auth_client.set_custom_user_claims(uid, {"role": "gym_admin", "gymId": gym_id})
        
        return uid
    except Exception as e:
        print(f"Error creating gym admin: {e}")
        return None

async def update_gym_admin(admin_id: str, admin_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a gym admin's profile and gym data
    
    Args:
        admin_id: Admin user ID
        admin_data: Admin data to update
        
    Returns:
        Updated admin data or None if failed
    """
    db = get_firestore_client()
    
    try:
        # First check if the admin exists
        admin = await get_user_by_uid(admin_id)
        if not admin or admin.get("role") != "gym_admin":
            return None
            
        gym_id = admin.get("gymId")
        if not gym_id:
            return None
            
        # Update admin document
        admin_update = {
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        
        # Add fields to update in admin document
        for key, value in admin_data.items():
            if key in ["displayName", "photoURL", "status"]:
                admin_update[key] = value
        
        # Update gym document
        gym_update = {
            "updatedAt": firestore.SERVER_TIMESTAMP,
        }
        
        # Add fields to update in gym document
        gym_fields = [
            "gymName", "gymLocation", "gymDescription", "gymFacilities",
            "gymHours", "gymContactEmail", "gymContactPhone", "gymPhotos"
        ]
        
        for key, value in admin_data.items():
            if key in gym_fields:
                gym_update[key] = value
                # Also update in admin document
                admin_update[key] = value
        
        # Update documents
        db.collection(GYM_ADMIN_COLLECTION).document(admin_id).update(admin_update)
        db.collection(GYMS_COLLECTION).document(gym_id).update(gym_update)
        
        # Get updated admin
        updated_admin = await get_user_by_uid(admin_id)
        return updated_admin
    except Exception as e:
        print(f"Error updating gym admin: {e}")
        return None

async def upload_gym_photo(admin_id: str, file) -> Optional[str]:
    """
    Upload a photo for the gym
    
    Args:
        admin_id: Admin user ID
        file: Uploaded file
        
    Returns:
        URL of the uploaded photo or None if failed
    """
    try:
        # First check if the admin exists
        admin = await get_user_by_uid(admin_id)
        if not admin or admin.get("role") != "gym_admin":
            return None
            
        gym_id = admin.get("gymId")
        if not gym_id:
            return None
        
        # Create a unique filename
        filename = f"{gym_id}/{uuid.uuid4()}-{file.filename}"
        
        # Upload to Firebase Storage
        bucket = storage.bucket()
        blob = bucket.blob(filename)
        
        # Read file content
        contents = await file.read()
        
        # Upload to Firebase Storage
        blob.upload_from_string(
            contents,
            content_type=file.content_type
        )
        
        # Make the blob publicly accessible
        blob.make_public()
        
        # Get the public URL
        photo_url = blob.public_url
        
        # Update gym photos in Firestore
        db = get_firestore_client()
        
        # Get current photos
        gym_doc = db.collection(GYMS_COLLECTION).document(gym_id).get()
        gym_data = gym_doc.to_dict()
        current_photos = gym_data.get("gymPhotos", [])
        
        # Add new photo
        current_photos.append(photo_url)
        
        # Update gym document
        db.collection(GYMS_COLLECTION).document(gym_id).update({
            "gymPhotos": current_photos,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        # Also update admin document
        db.collection(GYM_ADMIN_COLLECTION).document(admin_id).update({
            "gymPhotos": current_photos,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return photo_url
    except Exception as e:
        print(f"Error uploading gym photo: {e}")
        return None

async def get_gym_stats(gym_id: str) -> Dict[str, Any]:
    """
    Get a gym's statistics
    
    Args:
        gym_id: Gym ID
        
    Returns:
        Gym statistics
    """
    db = get_firestore_client()
    
    try:
        # Get gym data
        gym_doc = db.collection(GYMS_COLLECTION).document(gym_id).get()
        if not gym_doc.exists:
            return {
                "memberCount": 0,
                "activeMembers": 0,
                "trainerCount": 0,
                "totalCheckins": 0,
                "popularHours": {},
                "popularFacilities": {}
            }
            
        gym_data = gym_doc.to_dict()
        
        # Get member count
        member_count = gym_data.get("memberCount", 0)
        
        # Get active members (members who checked in today)
        today = datetime.now().strftime("%Y-%m-%d")
        active_members_query = db.collection(CHECKINS_COLLECTION).where("gymId", "==", gym_id).where("date", "==", today)
        active_members = set()
        for checkin in active_members_query.stream():
            checkin_data = checkin.to_dict()
            active_members.add(checkin_data.get("userId"))
        
        active_member_count = len(active_members)
        
        # Get trainer count
        trainer_count = gym_data.get("trainerCount", 0)
        
        # Get total checkins
        checkins_query = db.collection(CHECKINS_COLLECTION).where("gymId", "==", gym_id)
        total_checkins = len(list(checkins_query.stream()))
        
        # Get popular hours
        popular_hours = {}
        for checkin in checkins_query.stream():
            checkin_data = checkin.to_dict()
            hour = checkin_data.get("hour")
            if hour:
                popular_hours[hour] = popular_hours.get(hour, 0) + 1
        
        # Get popular facilities
        popular_facilities = {}
        for checkin in checkins_query.stream():
            checkin_data = checkin.to_dict()
            facilities = checkin_data.get("facilities", [])
            for facility in facilities:
                popular_facilities[facility] = popular_facilities.get(facility, 0) + 1
        
        return {
            "memberCount": member_count,
            "activeMembers": active_member_count,
            "trainerCount": trainer_count,
            "totalCheckins": total_checkins,
            "popularHours": popular_hours,
            "popularFacilities": popular_facilities
        }
    except Exception as e:
        print(f"Error getting gym stats: {e}")
        return {
            "memberCount": 0,
            "activeMembers": 0,
            "trainerCount": 0,
            "totalCheckins": 0,
            "popularHours": {},
            "popularFacilities": {}
        }

async def get_gym_members(
    gym_id: str,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    membership_type: Optional[str] = None,
    active_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get members of a gym
    
    Args:
        gym_id: Gym ID
        skip: Number of members to skip
        limit: Maximum number of members to return
        search: Optional search query
        membership_type: Optional membership type filter
        active_only: Whether to get only active members
        
    Returns:
        List of gym members
    """
    db = get_firestore_client()
    
    try:
        # Query gym members
        members_query = db.collection(GYM_MEMBERS_COLLECTION).where("gymId", "==", gym_id)
        
        # Apply membership type filter
        if membership_type:
            members_query = members_query.where("membershipType", "==", membership_type)
        
        # Get members
        members = []
        for member_doc in members_query.stream():
            member_data = member_doc.to_dict()
            
            # Get user data
            user_id = member_data.get("userId")
            if user_id:
                user = await get_user_by_uid(user_id)
                if user:
                    # Combine user and membership data
                    member_data.update({
                        "uid": user_id,
                        "displayName": user.get("displayName"),
                        "photoURL": user.get("photoURL"),
                    })
                    members.append(member_data)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            members = [
                member for member in members
                if search_lower in member.get("displayName", "").lower()
            ]
        
        # Apply active filter if requested
        if active_only:
            today = datetime.now().strftime("%Y-%m-%d")
            members = [
                member for member in members
                if member.get("lastCheckin", "").startswith(today)
            ]
        
        # Sort by join date
        members.sort(key=lambda x: x.get("joinDate", ""), reverse=True)
        
        # Apply pagination
        paginated_members = members[skip:skip + limit]
        
        return paginated_members
    except Exception as e:
        print(f"Error getting gym members: {e}")
        return []

async def get_gym_trainers(
    gym_id: str,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    speciality: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get trainers of a gym
    
    Args:
        gym_id: Gym ID
        skip: Number of trainers to skip
        limit: Maximum number of trainers to return
        search: Optional search query
        speciality: Optional speciality filter
        
    Returns:
        List of gym trainers
    """
    db = get_firestore_client()
    
    try:
        # Query trainers with the given gym ID
        trainers_query = db.collection(TRAINERS_COLLECTION).where("gymId", "==", gym_id)
        
        # Get trainers
        trainers = []
        for trainer_doc in trainers_query.stream():
            trainer_data = trainer_doc.to_dict()
            trainer_data["uid"] = trainer_doc.id
            trainers.append(trainer_data)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            trainers = [
                trainer for trainer in trainers
                if search_lower in trainer.get("displayName", "").lower()
            ]
        
        # Apply speciality filter if provided
        if speciality:
            trainers = [
                trainer for trainer in trainers
                if speciality in trainer.get("specialities", [])
            ]
        
        # Sort by rating
        trainers.sort(key=lambda x: x.get("rating", 0), reverse=True)
        
        # Apply pagination
        paginated_trainers = trainers[skip:skip + limit]
        
        # Add client and session counts
        for trainer in paginated_trainers:
            trainer_id = trainer.get("uid")
            
            # Count clients
            clients_query = db.collection("trainerClients").where("trainerId", "==", trainer_id)
            client_count = len(list(clients_query.stream()))
            trainer["clientCount"] = client_count
            
            # Count sessions
            sessions_query = db.collection("trainerSessions").where("trainerId", "==", trainer_id)
            session_count = len(list(sessions_query.stream()))
            trainer["sessionCount"] = session_count
        
        return paginated_trainers
    except Exception as e:
        print(f"Error getting gym trainers: {e}")
        return []

async def add_member_to_gym(
    gym_id: str,
    user_id: str,
    membership_data: Dict[str, Any]
) -> bool:
    """
    Add a user as a member to a gym
    
    Args:
        gym_id: Gym ID
        user_id: User ID
        membership_data: Membership data
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if user exists
        user = await get_user_by_uid(user_id)
        if not user:
            return False
        
        # Check if gym exists
        gym = await get_gym_by_id(gym_id)
        if not gym:
            return False
        
        # Check if user is already a member of this gym
        member_doc = db.collection(GYM_MEMBERS_COLLECTION).document(f"{gym_id}_{user_id}").get()
        if member_doc.exists:
            # Update membership
            db.collection(GYM_MEMBERS_COLLECTION).document(f"{gym_id}_{user_id}").update({
                "membershipType": membership_data.get("membershipType"),
                "membershipExpiration": membership_data.get("membershipExpiration"),
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
        else:
            # Create new membership
            membership = {
                "userId": user_id,
                "gymId": gym_id,
                "joinDate": firestore.SERVER_TIMESTAMP,
                "membershipType": membership_data.get("membershipType", "Standard"),
                "membershipExpiration": membership_data.get("membershipExpiration"),
                "checkinCount": 0,
                "lastCheckin": None,
                "createdAt": firestore.SERVER_TIMESTAMP,
                "updatedAt": firestore.SERVER_TIMESTAMP
            }
            
            # Add member to gym
            db.collection(GYM_MEMBERS_COLLECTION).document(f"{gym_id}_{user_id}").set(membership)
            
            # Update member count in gym
            db.collection(GYMS_COLLECTION).document(gym_id).update({
                "memberCount": firestore.Increment(1),
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
            
            # Update user's gym ID
            db.collection(USERS_COLLECTION).document(user_id).update({
                "gymId": gym_id,
                "updatedAt": firestore.SERVER_TIMESTAMP
            })
        
        return True
    except Exception as e:
        print(f"Error adding member to gym: {e}")
        return False

async def add_trainer_to_gym(
    gym_id: str,
    trainer_id: str
) -> bool:
    """
    Add a trainer to a gym
    
    Args:
        gym_id: Gym ID
        trainer_id: Trainer ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if trainer exists
        trainer = await get_user_by_uid(trainer_id)
        if not trainer or trainer.get("role") != "trainer":
            return False
        
        # Check if gym exists
        gym = await get_gym_by_id(gym_id)
        if not gym:
            return False
        
        # Update trainer's gym ID
        db.collection(TRAINERS_COLLECTION).document(trainer_id).update({
            "gymId": gym_id,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        # Update trainer count in gym
        db.collection(GYMS_COLLECTION).document(gym_id).update({
            "trainerCount": firestore.Increment(1),
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return True
    except Exception as e:
        print(f"Error adding trainer to gym: {e}")
        return False

async def remove_member_from_gym(
    gym_id: str,
    user_id: str
) -> bool:
    """
    Remove a member from a gym
    
    Args:
        gym_id: Gym ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if membership exists
        member_doc = db.collection(GYM_MEMBERS_COLLECTION).document(f"{gym_id}_{user_id}").get()
        if not member_doc.exists:
            return False
        
        # Delete membership
        db.collection(GYM_MEMBERS_COLLECTION).document(f"{gym_id}_{user_id}").delete()
        
        # Update member count in gym
        db.collection(GYMS_COLLECTION).document(gym_id).update({
            "memberCount": firestore.Increment(-1),
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        # Update user's gym ID
        db.collection(USERS_COLLECTION).document(user_id).update({
            "gymId": None,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return True
    except Exception as e:
        print(f"Error removing member from gym: {e}")
        return False

async def remove_trainer_from_gym(
    gym_id: str,
    trainer_id: str
) -> bool:
    """
    Remove a trainer from a gym
    
    Args:
        gym_id: Gym ID
        trainer_id: Trainer ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if trainer belongs to this gym
        trainer_doc = db.collection(TRAINERS_COLLECTION).document(trainer_id).get()
        if not trainer_doc.exists:
            return False
            
        trainer_data = trainer_doc.to_dict()
        if trainer_data.get("gymId") != gym_id:
            return False
        
        # Update trainer's gym ID
        db.collection(TRAINERS_COLLECTION).document(trainer_id).update({
            "gymId": None,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        # Update trainer count in gym
        db.collection(GYMS_COLLECTION).document(gym_id).update({
            "trainerCount": firestore.Increment(-1),
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return True
    except Exception as e:
        print(f"Error removing trainer from gym: {e}")
        return False

async def list_gyms(
    skip: int = 0, 
    limit: int = 20, 
    search: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    facilities: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    List gyms with optional filtering
    
    Args:
        skip: Number of gyms to skip
        limit: Maximum number of gyms to return
        search: Optional search query
        filters: Optional filters
        facilities: Optional list of facilities to filter by
        
    Returns:
        List of gyms
    """
    db = get_firestore_client()
    
    try:
        # Start with base query
        query = db.collection(GYMS_COLLECTION)
        
        # Apply location filter if provided
        if filters and filters.get("location"):
            query = query.where("gymLocation", "==", filters["location"])
        
        # Execute query
        results = query.stream()
        gyms = []
        
        for doc in results:
            gym_data = doc.to_dict()
            gym_data["gymId"] = doc.id
            gyms.append(gym_data)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            gyms = [
                gym for gym in gyms
                if search_lower in gym.get("gymName", "").lower() or
                search_lower in gym.get("gymLocation", "").lower() or
                search_lower in gym.get("gymDescription", "").lower()
            ]
        
        # Apply facilities filter if provided
        if facilities:
            gyms = [
                gym for gym in gyms
                if all(facility in gym.get("gymFacilities", []) for facility in facilities)
            ]
        
        # Sort by member count
        gyms.sort(key=lambda x: x.get("memberCount", 0), reverse=True)
        
        # Apply pagination
        paginated_gyms = gyms[skip:skip + limit]
        
        return paginated_gyms
    except Exception as e:
        print(f"Error listing gyms: {e}")
        return []