from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from app.schemas.connection import (
    ConnectionRequest,
    ConnectionAction,
    ConnectionResponse,
    ConnectionList
)
from app.core.security import get_current_user, get_current_active_user
from app.services import connection_service

router = APIRouter(prefix="/api/v1/connections")

@router.get("/", response_model=ConnectionList)
async def get_connections(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = "accepted"
):
    """
    Get user's connections
    """
    connections = await connection_service.get_connections(
        current_user["uid"],
        skip=skip,
        limit=limit,
        status=status
    )
    return {
        "total": len(connections),
        "connections": connections
    }

@router.get("/requests", response_model=ConnectionList)
async def get_connection_requests(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get pending connection requests for the user
    """
    connections = await connection_service.get_connection_requests(
        current_user["uid"],
        skip=skip,
        limit=limit
    )
    return {
        "total": len(connections),
        "connections": connections
    }

@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific connection
    """
    connection = await connection_service.get_connection(connection_id, current_user["uid"])
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    return connection

@router.post("/{user_id}", response_model=ConnectionResponse)
async def send_connection_request(
    user_id: str,
    request_data: ConnectionRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Send a connection request to another user
    """
    if user_id == current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send connection request to yourself"
        )
    
    connection = await connection_service.send_connection_request(
        current_user["uid"],
        user_id,
        request_data.message
    )
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send connection request"
        )
    
    return connection

@router.put("/{connection_id}", response_model=ConnectionResponse)
async def respond_to_connection_request(
    connection_id: str,
    action_data: ConnectionAction,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Respond to a connection request (accept, reject, block)
    """
    action = action_data.action.lower()
    if action not in ["accept", "reject", "block"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be 'accept', 'reject', or 'block'"
        )
    
    connection = await connection_service.respond_to_connection_request(
        connection_id,
        current_user["uid"],
        action
    )
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to respond to connection request"
        )
    
    return connection

@router.delete("/{connection_id}")
async def remove_connection(
    connection_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Remove a connection
    """
    success = await connection_service.remove_connection(connection_id, current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to remove connection"
        )
    return {"message": "Connection removed successfully"}

@router.get("/check/{user_id}")
async def check_connection_status(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Check connection status with another user
    """
    if user_id == current_user["uid"]:
        return {"status": "self"}
    
    status = await connection_service.check_connection_status(current_user["uid"], user_id)
    return {"status": status}

@router.get("/suggested")
async def get_suggested_connections(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get suggested connections based on shared interests, gym, etc.
    """
    suggestions = await connection_service.get_suggested_connections(
        current_user["uid"],
        limit=limit
    )
    
    return {
        "total": len(suggestions),
        "suggestions": suggestions
    }