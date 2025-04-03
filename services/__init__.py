"""
Business logic service modules
"""

# Export all services for easy importing
from app.services.user_service import *
from app.services.trainer_service import *
from app.services.gym_admin_service import *
from app.services.social_service import *
from app.services.connection_service import *
from app.services.chat_service import *
from app.services.notification_service import *
from app.services.milestone_service import *

# Define available services
__all__ = [
    # User services
    "get_user_by_id",
    "update_user",
    "get_active_users",
    "list_users",
    "get_user_stats",
    "create_user",
    
    # Trainer services
    "get_trainer_by_id",
    "update_trainer",
    "get_active_trainers",
    "list_trainers",
    "get_trainer_stats",
    "get_trainer_availability",
    "add_availability_slot",
    "remove_availability_slot",
    "create_trainer",
    
    # Gym admin services
    "get_gym_by_id",
    "get_gym_by_admin_id",
    "update_gym_admin",
    "upload_gym_photo",
    "get_gym_stats",
    "get_gym_members",
    "get_gym_trainers",
    "add_member_to_gym",
    "add_trainer_to_gym",
    "remove_member_from_gym",
    "remove_trainer_from_gym",
    "list_gyms",
    "create_gym_admin",
    
    # Social services
    "get_feed",
    "get_user_posts",
    "get_gym_posts",
    "create_post",
    "get_post",
    "update_post",
    "delete_post",
    "upload_post_media",
    "like_post",
    "unlike_post",
    "get_post_comments",
    "create_comment",
    "get_comment",
    "update_comment",
    "delete_comment",
    "like_comment",
    "unlike_comment",
    
    # Connection services
    "get_connections",
    "get_connection_requests",
    "get_connection",
    "send_connection_request",
    "respond_to_connection_request",
    "remove_connection",
    "check_connection_status",
    "get_suggested_connections",
    
    # Chat services
    "get_conversations",
    "create_conversation",
    "get_conversation",
    "update_conversation",
    "delete_conversation",
    "get_messages",
    "send_message",
    "update_message",
    "upload_message_media",
    "get_or_create_conversation",
    
    # Notification services
    "get_notifications",
    "get_unread_count",
    "get_notification",
    "update_notification",
    "mark_all_as_read",
    "delete_notification",
    "delete_all_notifications",
    "create_notification",
    
    # Milestone services
    "get_user_milestones",
    "get_achievements",
    "get_achievement",
    "get_challenges",
    "get_challenge",
    "join_challenge",
    "update_challenge_progress",
    "get_leaderboard",
    "check_achievement_progress"
]