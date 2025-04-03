from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from app.schemas.notification import NotificationResponse, NotificationUpdate, NotificationList
from app.core.security import get_current_user, get_current_active_user
from app.services import notification_service

router = APIRouter(prefix="/api/v1/notifications")

@router.get("/", response_model=NotificationList)
async def get_notifications(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = False
):
    """
    Get user's notifications
    """
    notifications, unread_count = await notification_service.get_notifications(
        current_user["uid"],
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    return {
        "total": len(notifications),
        "unreadCount": unread_count,
        "notifications": notifications
    }

@router.get("/unread-count")
async def get_unread_count(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get count of unread notifications
    """
    unread_count = await notification_service.get_unread_count(current_user["uid"])
    return {"unreadCount": unread_count}

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific notification
    """
    notification = await notification_service.get_notification(notification_id, current_user["uid"])
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update a notification (mark as read)
    """
    notification = await notification_service.update_notification(
        notification_id,
        current_user["uid"],
        notification_update.dict(exclude_unset=True)
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update notification"
        )
    
    return notification

@router.put("/", response_model=NotificationList)
async def mark_all_as_read(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Mark all notifications as read
    """
    notifications = await notification_service.mark_all_as_read(current_user["uid"])
    return {
        "total": len(notifications),
        "unreadCount": 0,
        "notifications": notifications
    }

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a notification
    """
    success = await notification_service.delete_notification(notification_id, current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete notification"
        )
    return {"message": "Notification deleted successfully"}

@router.delete("/")
async def delete_all_notifications(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete all notifications
    """
    success = await notification_service.delete_all_notifications(current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete notifications"
        )
    return {"message": "All notifications deleted successfully"}