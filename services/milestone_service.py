from typing import Dict, List, Any, Optional, Tuple
from app.db.firebase_client import get_user_by_uid
from app.config.firebase import get_firestore_client
from firebase_admin import firestore
import uuid
from datetime import datetime, timedelta

# Collection names
USERS_COLLECTION = "users"
ACHIEVEMENTS_COLLECTION = "achievements"
CHALLENGES_COLLECTION = "challenges"
CHALLENGE_PARTICIPANTS_COLLECTION = "challengeParticipants"
USER_ACHIEVEMENTS_COLLECTION = "userAchievements"
MILESTONE_ACTIVITIES_COLLECTION = "milestoneActivities"
NOTIFICATIONS_COLLECTION = "notifications"

async def get_user_milestones(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user's milestone data
    
    Args:
        user_id: User ID
        
    Returns:
        User milestone data or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Get user data
        user = await get_user_by_uid(user_id)
        if not user:
            return None
        
        # Get user level and points
        level = user.get("level", 1)
        total_points = user.get("experiencePoints", 0)
        
        # Calculate points needed for next level
        # Formula: 100 * (level ^ 1.5)
        points_for_next_level = int(100 * (level ** 1.5))
        
        # Calculate progress percentage
        points_progress = min(1.0, total_points / points_for_next_level) if points_for_next_level > 0 else 0
        
        # Get user achievements (top 5 most recent)
        achievements = []
        user_achievements_query = db.collection(USER_ACHIEVEMENTS_COLLECTION).where(
            "userId", "==", user_id
        ).where("isUnlocked", "==", True).order_by("unlockedAt", direction=firestore.Query.DESCENDING).limit(5)
        
        for ach_doc in user_achievements_query.stream():
            ach_data = ach_doc.to_dict()
            achievement_id = ach_data.get("achievementId")
            
            # Get achievement details
            achievement_doc = db.collection(ACHIEVEMENTS_COLLECTION).document(achievement_id).get()
            if achievement_doc.exists:
                achievement_data = achievement_doc.to_dict()
                
                achievement = {
                    "id": achievement_id,
                    "title": achievement_data.get("title"),
                    "description": achievement_data.get("description"),
                    "category": achievement_data.get("category"),
                    "icon": achievement_data.get("icon"),
                    "requirements": achievement_data.get("requirements"),
                    "points": achievement_data.get("points"),
                    "isUnlocked": True,
                    "progress": ach_data.get("progress"),
                    "maxProgress": ach_data.get("maxProgress"),
                    "progressPercentage": 1.0,
                    "unlockedAt": ach_data.get("unlockedAt")
                }
                
                achievements.append(achievement)
        
        # Get user's active challenges
        active_challenges = []
        challenge_participants_query = db.collection(CHALLENGE_PARTICIPANTS_COLLECTION).where(
            "userId", "==", user_id
        ).where("status", "==", "active")
        
        for part_doc in challenge_participants_query.stream():
            part_data = part_doc.to_dict()
            challenge_id = part_data.get("challengeId")
            
            # Get challenge details
            challenge_doc = db.collection(CHALLENGES_COLLECTION).document(challenge_id).get()
            if challenge_doc.exists:
                challenge_data = challenge_doc.to_dict()
                
                # Calculate progress percentage
                progress = part_data.get("progress", 0)
                max_progress = challenge_data.get("requirements", {}).get("targetValue", 100)
                progress_percentage = min(1.0, progress / max_progress) if max_progress > 0 else 0
                
                challenge = {
                    "id": challenge_id,
                    "title": challenge_data.get("title"),
                    "description": challenge_data.get("description"),
                    "category": challenge_data.get("category"),
                    "icon": challenge_data.get("icon"),
                    "requirements": challenge_data.get("requirements"),
                    "points": challenge_data.get("points"),
                    "status": "active",
                    "progress": progress,
                    "maxProgress": max_progress,
                    "progressPercentage": progress_percentage,
                    "startDate": challenge_data.get("startDate"),
                    "endDate": challenge_data.get("endDate"),
                    "participants": challenge_data.get("participantCount", 0),
                    "isJoined": True,
                    "createdBy": challenge_data.get("createdBy")
                }
                
                active_challenges.append(challenge)
        
        # Get user's completed challenges (top 3)
        completed_challenges = []
        completed_participants_query = db.collection(CHALLENGE_PARTICIPANTS_COLLECTION).where(
            "userId", "==", user_id
        ).where("status", "==", "completed").order_by("completedAt", direction=firestore.Query.DESCENDING).limit(3)
        
        for part_doc in completed_participants_query.stream():
            part_data = part_doc.to_dict()
            challenge_id = part_data.get("challengeId")
            
            # Get challenge details
            challenge_doc = db.collection(CHALLENGES_COLLECTION).document(challenge_id).get()
            if challenge_doc.exists:
                challenge_data = challenge_doc.to_dict()
                
                challenge = {
                    "id": challenge_id,
                    "title": challenge_data.get("title"),
                    "description": challenge_data.get("description"),
                    "category": challenge_data.get("category"),
                    "icon": challenge_data.get("icon"),
                    "requirements": challenge_data.get("requirements"),
                    "points": challenge_data.get("points"),
                    "status": "completed",
                    "progress": part_data.get("progress"),
                    "maxProgress": challenge_data.get("requirements", {}).get("targetValue", 100),
                    "progressPercentage": 1.0,
                    "startDate": challenge_data.get("startDate"),
                    "endDate": challenge_data.get("endDate"),
                    "participants": challenge_data.get("participantCount", 0),
                    "isJoined": True,
                    "createdBy": challenge_data.get("createdBy")
                }
                
                completed_challenges.append(challenge)
        
        # Get recent milestone activities
        recent_activities = []
        activities_query = db.collection(MILESTONE_ACTIVITIES_COLLECTION).where(
            "userId", "==", user_id
        ).order_by("createdAt", direction=firestore.Query.DESCENDING).limit(10)
        
        for act_doc in activities_query.stream():
            activity_data = act_doc.to_dict()
            activity_data["id"] = act_doc.id
            recent_activities.append(activity_data)
        
        # Return milestone data
        return {
            "level": level,
            "totalPoints": total_points,
            "pointsForNextLevel": points_for_next_level,
            "pointsProgress": points_progress,
            "achievements": achievements,
            "challengesActive": active_challenges,
            "challengesCompleted": completed_challenges,
            "recentActivity": recent_activities
        }
    except Exception as e:
        print(f"Error getting user milestones: {e}")
        return None

async def get_achievements(
    user_id: str,
    category: Optional[str] = None,
    unlocked_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get achievements with user's progress
    
    Args:
        user_id: User ID
        category: Optional category filter
        unlocked_only: Whether to show only unlocked achievements
        
    Returns:
        List of achievements
    """
    db = get_firestore_client()
    
    try:
        # Get all achievements
        achievements_query = db.collection(ACHIEVEMENTS_COLLECTION)
        
        if category:
            achievements_query = achievements_query.where("category", "==", category)
        
        # Get user achievements
        user_achievements_query = db.collection(USER_ACHIEVEMENTS_COLLECTION).where("userId", "==", user_id)
        user_achievements = {}
        
        for user_ach_doc in user_achievements_query.stream():
            user_ach_data = user_ach_doc.to_dict()
            achievement_id = user_ach_data.get("achievementId")
            user_achievements[achievement_id] = user_ach_data
        
        # Process achievements
        achievements = []
        for ach_doc in achievements_query.stream():
            achievement_data = ach_doc.to_dict()
            achievement_id = ach_doc.id
            
            # Get user's progress for this achievement
            user_ach_data = user_achievements.get(achievement_id, {})
            is_unlocked = user_ach_data.get("isUnlocked", False)
            
            # Skip if unlocked_only and not unlocked
            if unlocked_only and not is_unlocked:
                continue
            
            # Get progress data
            progress = user_ach_data.get("progress", 0)
            max_progress = achievement_data.get("requirements", {}).get("targetValue", 100)
            progress_percentage = min(1.0, progress / max_progress) if max_progress > 0 else 0
            
            # Create achievement response
            achievement = {
                "id": achievement_id,
                "title": achievement_data.get("title"),
                "description": achievement_data.get("description"),
                "category": achievement_data.get("category"),
                "icon": achievement_data.get("icon"),
                "requirements": achievement_data.get("requirements"),
                "points": achievement_data.get("points"),
                "isUnlocked": is_unlocked,
                "progress": progress,
                "maxProgress": max_progress,
                "progressPercentage": progress_percentage,
                "unlockedAt": user_ach_data.get("unlockedAt")
            }
            
            achievements.append(achievement)
        
        # Sort achievements (unlocked first, then by progress percentage)
        achievements.sort(key=lambda x: (-int(x["isUnlocked"]), -x["progressPercentage"]))
        
        return achievements
    except Exception as e:
        print(f"Error getting achievements: {e}")
        return []

async def get_achievement(achievement_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific achievement with user's progress
    
    Args:
        achievement_id: Achievement ID
        user_id: User ID
        
    Returns:
        Achievement data or None if not found
    """
    db = get_firestore_client()
    
    try:
        # Get achievement
        ach_doc = db.collection(ACHIEVEMENTS_COLLECTION).document(achievement_id).get()
        if not ach_doc.exists:
            return None
        
        achievement_data = ach_doc.to_dict()
        
        # Get user achievement
        user_ach_query = db.collection(USER_ACHIEVEMENTS_COLLECTION).where(
            "userId", "==", user_id
        ).where("achievementId", "==", achievement_id)
        
        user_ach_docs = list(user_ach_query.stream())
        user_ach_data = user_ach_docs[0].to_dict() if user_ach_docs else {}
        
        is_unlocked = user_ach_data.get("isUnlocked", False)
        progress = user_ach_data.get("progress", 0)
        max_progress = achievement_data.get("requirements", {}).get("targetValue", 100)
        progress_percentage = min(1.0, progress / max_progress) if max_progress > 0 else 0
        
        # Create achievement response
        achievement = {
            "id": achievement_id,
            "title": achievement_data.get("title"),
            "description": achievement_data.get("description"),
            "category": achievement_data.get("category"),
            "icon": achievement_data.get("icon"),
            "requirements": achievement_data.get("requirements"),
            "points": achievement_data.get("points"),
            "isUnlocked": is_unlocked,
            "progress": progress,
            "maxProgress": max_progress,
            "progressPercentage": progress_percentage,
            "unlockedAt": user_ach_data.get("unlockedAt")
        }
        
        return achievement
    except Exception as e:
        print(f"Error getting achievement: {e}")
        return None

async def get_challenges(
    user_id: str,
    category: Optional[str] = None,
    status: Optional[str] = None,
    joined_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get challenges with user's progress
    
    Args:
        user_id: User ID
        category: Optional category filter
        status: Optional status filter (active, upcoming, completed)
        joined_only: Whether to show only challenges the user has joined
        
    Returns:
        List of challenges
    """
    db = get_firestore_client()
    
    try:
        # Get current date for filtering
        current_date = datetime.now()
        
        # Get all challenges
        challenges_query = db.collection(CHALLENGES_COLLECTION)
        
        if category:
            challenges_query = challenges_query.where("category", "==", category)
        
        # Apply status filter to query if possible
        if status == "active":
            challenges_query = challenges_query.where("startDate", "<=", current_date).where("endDate", ">=", current_date)
        elif status == "upcoming":
            challenges_query = challenges_query.where("startDate", ">", current_date)
        
        # Get user challenge participations
        part_query = db.collection(CHALLENGE_PARTICIPANTS_COLLECTION).where("userId", "==", user_id)
        user_participations = {}
        
        for part_doc in part_query.stream():
            part_data = part_doc.to_dict()
            challenge_id = part_data.get("challengeId")
            user_participations[challenge_id] = part_data
        
        # Process challenges
        challenges = []
        for chal_doc in challenges_query.stream():
            challenge_data = chal_doc.to_dict()
            challenge_id = chal_doc.id
            
            # Get challenge dates
            start_date = challenge_data.get("startDate")
            end_date = challenge_data.get("endDate")
            
            # Determine challenge status based on dates
            challenge_status = "active"
            if start_date > current_date:
                challenge_status = "upcoming"
            elif end_date < current_date:
                challenge_status = "completed"
            
            # Apply status filter
            if status and status != challenge_status:
                continue
            
            # Get user's participation for this challenge
            part_data = user_participations.get(challenge_id, {})
            is_joined = bool(part_data)
            
            # Skip if joined_only and not joined
            if joined_only and not is_joined:
                continue
            
            # Override status with user participation status if available
            if is_joined and part_data.get("status"):
                challenge_status = part_data.get("status")
            
            # Get progress data
            progress = part_data.get("progress", 0)
            max_progress = challenge_data.get("requirements", {}).get("targetValue", 100)
            progress_percentage = min(1.0, progress / max_progress) if max_progress > 0 else 0
            
            # Create challenge response
            challenge = {
                "id": challenge_id,
                "title": challenge_data.get("title"),
                "description": challenge_data.get("description"),
                "category": challenge_data.get("category"),
                "icon": challenge_data.get("icon"),
                "requirements": challenge_data.get("requirements"),
                "points": challenge_data.get("points"),
                "status": challenge_status,
                "progress": progress,
                "maxProgress": max_progress,
                "progressPercentage": progress_percentage,
                "startDate": start_date,
                "endDate": end_date,
                "participants": challenge_data.get("participantCount", 0),
                "isJoined": is_joined,
                "createdBy": challenge_data.get("createdBy")
            }
            
            challenges.append(challenge)
        
        # Sort challenges (active first, then upcoming, then by end date)
        def challenge_sort_key(challenge):
            status_order = {"active": 0, "upcoming": 1, "completed": 2, "failed": 3}
            status = challenge.get("status", "")
            return (status_order.get(status, 4), challenge.get("endDate", datetime.max))
            
        challenges.sort(key=challenge_sort_key)
        
        return challenges
    except Exception as e:
        print(f"Error getting challenges: {e}")
        return []

async def get_challenge(challenge_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific challenge with user's progress
    
    Args:
        challenge_id: Challenge ID
        user_id: User ID
        
    Returns:
        Challenge data or None if not found
    """
    db = get_firestore_client()
    
    try:
        # Get challenge
        chal_doc = db.collection(CHALLENGES_COLLECTION).document(challenge_id).get()
        if not chal_doc.exists:
            return None
        
        challenge_data = chal_doc.to_dict()
        
        # Get current date
        current_date = datetime.now()
        
        # Determine challenge status based on dates
        start_date = challenge_data.get("startDate")
        end_date = challenge_data.get("endDate")
        
        challenge_status = "active"
        if start_date > current_date:
            challenge_status = "upcoming"
        elif end_date < current_date:
            challenge_status = "completed"
        
        # Get user participation
        part_query = db.collection(CHALLENGE_PARTICIPANTS_COLLECTION).where(
            "userId", "==", user_id
        ).where("challengeId", "==", challenge_id)
        
        part_docs = list(part_query.stream())
        part_data = part_docs[0].to_dict() if part_docs else {}
        
        is_joined = bool(part_data)
        
        # Override status with user participation status if available
        if is_joined and part_data.get("status"):
            challenge_status = part_data.get("status")
        
        # Get progress data
        progress = part_data.get("progress", 0)
        max_progress = challenge_data.get("requirements", {}).get("targetValue", 100)
        progress_percentage = min(1.0, progress / max_progress) if max_progress > 0 else 0
        
        # Create challenge response
        challenge = {
            "id": challenge_id,
            "title": challenge_data.get("title"),
            "description": challenge_data.get("description"),
            "category": challenge_data.get("category"),
            "icon": challenge_data.get("icon"),
            "requirements": challenge_data.get("requirements"),
            "points": challenge_data.get("points"),
            "status": challenge_status,
            "progress": progress,
            "maxProgress": max_progress,
            "progressPercentage": progress_percentage,
            "startDate": start_date,
            "endDate": end_date,
            "participants": challenge_data.get("participantCount", 0),
            "isJoined": is_joined,
            "createdBy": challenge_data.get("createdBy")
        }
        
        return challenge
    except Exception as e:
        print(f"Error getting challenge: {e}")
        return None

async def join_challenge(challenge_id: str, user_id: str) -> bool:
    """
    Join a challenge
    
    Args:
        challenge_id: Challenge ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Get challenge
        chal_doc = db.collection(CHALLENGES_COLLECTION).document(challenge_id).get()
        if not chal_doc.exists:
            return False
        
        challenge_data = chal_doc.to_dict()
        
        # Check if challenge is still open for joining
        current_date = datetime.now()
        end_date = challenge_data.get("endDate")
        
        if end_date < current_date:
            return False  # Challenge has ended
        
        # Check if user already joined
        part_query = db.collection(CHALLENGE_PARTICIPANTS_COLLECTION).where(
            "userId", "==", user_id
        ).where("challengeId", "==", challenge_id)
        
        part_docs = list(part_query.stream())
        if part_docs:
            return True  # Already joined
        
        # Get user data
        user = await get_user_by_uid(user_id)
        if not user:
            return False
        
        # Create participation document
        participation_id = f"{challenge_id}_{user_id}"
        
        participation_data = {
            "userId": user_id,
            "userName": user.get("displayName", ""),
            "userPhoto": user.get("photoURL"),
            "challengeId": challenge_id,
            "progress": 0,
            "status": "active",
            "joinedAt": firestore.SERVER_TIMESTAMP,
            "lastUpdated": firestore.SERVER_TIMESTAMP
        }
        
        # Add transaction to update both participation and challenge
        transaction = db.transaction()
        
        @firestore.transactional
        def update_in_transaction(transaction, part_ref, chal_ref):
            # Add participation
            transaction.set(part_ref, participation_data)
            
            # Increment participant count
            transaction.update(chal_ref, {"participantCount": firestore.Increment(1)})
            
            return True
        
        # Run transaction
        part_ref = db.collection(CHALLENGE_PARTICIPANTS_COLLECTION).document(participation_id)
        chal_ref = db.collection(CHALLENGES_COLLECTION).document(challenge_id)
        
        success = update_in_transaction(transaction, part_ref, chal_ref)
        
        if success:
            # Create activity
            activity_id = str(uuid.uuid4())
            
            activity_data = {
                "userId": user_id,
                "type": "challenge_joined",
                "message": f"Joined the {challenge_data.get('title')} challenge",
                "targetId": challenge_id,
                "targetType": "challenge",
                "createdAt": firestore.SERVER_TIMESTAMP
            }
            
            db.collection(MILESTONE_ACTIVITIES_COLLECTION).document(activity_id).set(activity_data)
        
        return success
    except Exception as e:
        print(f"Error joining challenge: {e}")
        return False

async def update_challenge_progress(
    challenge_id: str,
    user_id: str,
    progress_value: int,
    notes: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update progress for a challenge
    
    Args:
        challenge_id: Challenge ID
        user_id: User ID
        progress_value: New progress value
        notes: Optional notes
        
    Returns:
        Updated challenge or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Get challenge
        chal_doc = db.collection(CHALLENGES_COLLECTION).document(challenge_id).get()
        if not chal_doc.exists:
            return None
        
        challenge_data = chal_doc.to_dict()
        
        # Check if challenge is active
        current_date = datetime.now()
        start_date = challenge_data.get("startDate")
        end_date = challenge_data.get("endDate")
        
        if start_date > current_date or end_date < current_date:
            return None  # Challenge is not active
        
        # Get user participation
        participation_id = f"{challenge_id}_{user_id}"
        part_doc = db.collection(CHALLENGE_PARTICIPANTS_COLLECTION).document(participation_id).get()
        
        if not part_doc.exists:
            return None  # User hasn't joined
        
        part_data = part_doc.to_dict()
        
        # Skip if already completed
        if part_data.get("status") == "completed":
            return await get_challenge(challenge_id, user_id)
        
        # Get target value
        target_value = challenge_data.get("requirements", {}).get("targetValue", 100)
        
        # Check if challenge is completed with this update
        is_completed = progress_value >= target_value
        new_status = "completed" if is_completed else "active"
        
        # Update participation
        update_data = {
            "progress": progress_value,
            "lastUpdated": firestore.SERVER_TIMESTAMP
        }
        
        if is_completed:
            update_data["status"] = "completed"
            update_data["completedAt"] = firestore.SERVER_TIMESTAMP
        
        if notes:
            update_data["notes"] = notes
        
        db.collection(CHALLENGE_PARTICIPANTS_COLLECTION).document(participation_id).update(update_data)
        
        # If completed, update user's points and create activity
        if is_completed:
            # Add points to user
            points = challenge_data.get("points", 0)
            
            user_ref = db.collection(USERS_COLLECTION).document(user_id)
            user_ref.update({
                "experiencePoints": firestore.Increment(points)
            })
            
            # Check if level up is needed
            user = await get_user_by_uid(user_id)
            current_level = user.get("level", 1)
            total_points = user.get("experiencePoints", 0) + points
            
            # Formula: level = floor(1 + sqrt(total_points / 100))
            import math
            new_level = math.floor(1 + math.sqrt(total_points / 100))
            
            if new_level > current_level:
                # Level up
                user_ref.update({"level": new_level})
                
                # Create level up notification
                notification_id = str(uuid.uuid4())
                
                notification_data = {
                    "userId": user_id,
                    "type": "level_up",
                    "message": f"You've reached level {new_level}!",
                    "data": {
                        "newLevel": new_level,
                        "oldLevel": current_level
                    },
                    "isRead": False,
                    "createdAt": firestore.SERVER_TIMESTAMP
                }
                
                db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification_data)
                
                # Create level up activity
                activity_id = str(uuid.uuid4())
                
                activity_data = {
                    "userId": user_id,
                    "type": "level_up",
                    "message": f"Reached level {new_level}",
                    "data": {
                        "newLevel": new_level,
                        "oldLevel": current_level
                    },
                    "createdAt": firestore.SERVER_TIMESTAMP
                }
                
                db.collection(MILESTONE_ACTIVITIES_COLLECTION).document(activity_id).set(activity_data)
            
            # Create challenge completed notification
            notification_id = str(uuid.uuid4())
            
            notification_data = {
                "userId": user_id,
                "type": "challenge_completed",
                "message": f"You've completed the {challenge_data.get('title')} challenge!",
                "data": {
                    "challengeId": challenge_id,
                    "pointsEarned": points
                },
                "isRead": False,
                "createdAt": firestore.SERVER_TIMESTAMP
            }
            
            db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification_data)
            
            # Create challenge completed activity
            activity_id = str(uuid.uuid4())
            
            activity_data = {
                "userId": user_id,
                "type": "challenge_completed",
                "message": f"Completed the {challenge_data.get('title')} challenge",
                "targetId": challenge_id,
                "targetType": "challenge",
                "data": {
                    "pointsEarned": points
                },
                "createdAt": firestore.SERVER_TIMESTAMP
            }
            
            db.collection(MILESTONE_ACTIVITIES_COLLECTION).document(activity_id).set(activity_data)
        
        # Return updated challenge
        return await get_challenge(challenge_id, user_id)
    except Exception as e:
        print(f"Error updating challenge progress: {e}")
        return None

async def get_leaderboard(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    time_period: str = "all"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get leaderboard of users by points/level
    
    Args:
        user_id: User ID
        skip: Number of entries to skip
        limit: Maximum number of entries to return
        time_period: Time period filter (all, week, month)
        
    Returns:
        Tuple of (leaderboard entries, user's position)
    """
    db = get_firestore_client()
    
    try:
        # Get all users ordered by level and experience points
        users_query = db.collection(USERS_COLLECTION).order_by("level", direction=firestore.Query.DESCENDING).order_by("experiencePoints", direction=firestore.Query.DESCENDING)
        
        # Process users for leaderboard
        users = []
        user_position = 0
        position = 1
        
        # Process all users to find user position
        for user_doc in users_query.stream():
            user_data = user_doc.to_dict()
            
            if user_data.get("uid") == user_id:
                user_position = position
            
            # Create leaderboard entry
            entry = {
                "userId": user_data.get("uid"),
                "displayName": user_data.get("displayName", ""),
                "photoURL": user_data.get("photoURL"),
                "level": user_data.get("level", 1),
                "points": user_data.get("experiencePoints", 0),
                "achievements": user_data.get("achievementCount", 0),
                "position": position
            }
            
            users.append(entry)
            position += 1
        
        # Apply pagination
        paginated_users = users[skip:skip + limit]
        
        return paginated_users, user_position
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        return [], 0

async def check_achievement_progress(user_id: str, action_type: str, action_data: Dict[str, Any]) -> None:
    """
    Check and update achievement progress for a user action
    
    Args:
        user_id: User ID
        action_type: Type of action (workout, social, etc.)
        action_data: Action data
    """
    db = get_firestore_client()
    
    try:
        # Get user
        user = await get_user_by_uid(user_id)
        if not user:
            return
        
        # Get achievements that might be affected by this action
        achievements_query = db.collection(ACHIEVEMENTS_COLLECTION).where(
            "requirements.actionType", "==", action_type
        )
        
        # Process each achievement
        for ach_doc in achievements_query.stream():
            achievement_data = ach_doc.to_dict()
            achievement_id = ach_doc.id
            
            # Get requirements
            requirements = achievement_data.get("requirements", {})
            target_value = requirements.get("targetValue", 1)
            
            # Get user achievement status
            user_ach_query = db.collection(USER_ACHIEVEMENTS_COLLECTION).where(
                "userId", "==", user_id
            ).where("achievementId", "==", achievement_id)
            
            user_ach_docs = list(user_ach_query.stream())
            
            if not user_ach_docs:
                # Create user achievement with initial progress
                user_ach_id = f"{user_id}_{achievement_id}"
                
                user_ach_data = {
                    "userId": user_id,
                    "achievementId": achievement_id,
                    "progress": 1,  # Start with 1 progress
                    "maxProgress": target_value,
                    "isUnlocked": False,
                    "createdAt": firestore.SERVER_TIMESTAMP,
                    "updatedAt": firestore.SERVER_TIMESTAMP
                }
                
                db.collection(USER_ACHIEVEMENTS_COLLECTION).document(user_ach_id).set(user_ach_data)
            else:
                # Update existing user achievement
                user_ach_doc = user_ach_docs[0]
                user_ach_data = user_ach_doc.to_dict()
                
                # Skip if already unlocked
                if user_ach_data.get("isUnlocked", False):
                    continue
                
                # Increment progress
                current_progress = user_ach_data.get("progress", 0)
                new_progress = current_progress + 1
                
                # Check if achievement is unlocked
                is_unlocked = new_progress >= target_value
                
                update_data = {
                    "progress": new_progress,
                    "updatedAt": firestore.SERVER_TIMESTAMP
                }
                
                if is_unlocked:
                    update_data["isUnlocked"] = True
                    update_data["unlockedAt"] = firestore.SERVER_TIMESTAMP
                
                user_ach_doc.reference.update(update_data)
                
                # If unlocked, update user
                if is_unlocked:
                    # Add points to user
                    points = achievement_data.get("points", 0)
                    
                    user_ref = db.collection(USERS_COLLECTION).document(user_id)
                    user_ref.update({
                        "experiencePoints": firestore.Increment(points),
                        "achievementCount": firestore.Increment(1)
                    })
                    
                    # Check if level up is needed
                    current_level = user.get("level", 1)
                    total_points = user.get("experiencePoints", 0) + points
                    
                    # Formula: level = floor(1 + sqrt(total_points / 100))
                    import math
                    new_level = math.floor(1 + math.sqrt(total_points / 100))
                    
                    if new_level > current_level:
                        # Level up
                        user_ref.update({"level": new_level})
                        
                        # Create level up notification
                        notification_id = str(uuid.uuid4())
                        
                        notification_data = {
                            "userId": user_id,
                            "type": "level_up",
                            "message": f"You've reached level {new_level}!",
                            "data": {
                                "newLevel": new_level,
                                "oldLevel": current_level
                            },
                            "isRead": False,
                            "createdAt": firestore.SERVER_TIMESTAMP
                        }
                        
                        db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification_data)
                    
                    # Create achievement unlocked notification
                    notification_id = str(uuid.uuid4())
                    
                    notification_data = {
                        "userId": user_id,
                        "type": "achievement_unlocked",
                        "message": f"You've unlocked the {achievement_data.get('title')} achievement!",
                        "data": {
                            "achievementId": achievement_id,
                            "pointsEarned": points
                        },
                        "isRead": False,
                        "createdAt": firestore.SERVER_TIMESTAMP
                    }
                    
                    db.collection(NOTIFICATIONS_COLLECTION).document(notification_id).set(notification_data)
                    
                    # Create achievement unlocked activity
                    activity_id = str(uuid.uuid4())
                    
                    activity_data = {
                        "userId": user_id,
                        "type": "achievement_unlocked",
                        "message": f"Unlocked the {achievement_data.get('title')} achievement",
                        "targetId": achievement_id,
                        "targetType": "achievement",
                        "data": {
                            "pointsEarned": points
                        },
                        "createdAt": firestore.SERVER_TIMESTAMP
                    }
                    
                    db.collection(MILESTONE_ACTIVITIES_COLLECTION).document(activity_id).set(activity_data)
    except Exception as e:
        print(f"Error checking achievement progress: {e}")