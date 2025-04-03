from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from typing import Dict, List, Any, Optional
from app.schemas.social import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostList,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentList
)
from app.core.security import get_current_user, get_current_active_user
from app.services import social_service

router = APIRouter(prefix="/api/v1/social")

@router.get("/feed", response_model=PostList)
async def get_social_feed(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    filter_type: Optional[str] = None
):
    """
    Get posts for the user's social feed
    """
    posts = await social_service.get_feed(
        current_user["uid"],
        skip=skip,
        limit=limit,
        filter_type=filter_type
    )
    return {
        "total": len(posts),
        "posts": posts
    }

@router.get("/user/{user_id}", response_model=PostList)
async def get_user_posts(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get posts by a specific user
    """
    posts = await social_service.get_user_posts(
        user_id,
        current_user["uid"],
        skip=skip,
        limit=limit
    )
    return {
        "total": len(posts),
        "posts": posts
    }

@router.get("/gym/{gym_id}", response_model=PostList)
async def get_gym_posts(
    gym_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get posts for a specific gym
    """
    posts = await social_service.get_gym_posts(
        gym_id,
        current_user["uid"],
        skip=skip,
        limit=limit
    )
    return {
        "total": len(posts),
        "posts": posts
    }

@router.post("/posts", response_model=PostResponse)
async def create_post(
    post_data: PostCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new post
    """
    post = await social_service.create_post(current_user["uid"], post_data)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create post"
        )
    return post

@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a specific post
    """
    post = await social_service.get_post(post_id, current_user["uid"])
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post

@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_update: PostUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update a post
    """
    # Check if user is the post owner
    post = await social_service.get_post(post_id, current_user["uid"])
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if post["userId"] != current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )
    
    updated_post = await social_service.update_post(post_id, post_update)
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update post"
        )
    return updated_post

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a post
    """
    # Check if user is the post owner
    post = await social_service.get_post(post_id, current_user["uid"])
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if post["userId"] != current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )
    
    success = await social_service.delete_post(post_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete post"
        )
    return {"message": "Post deleted successfully"}

@router.post("/posts/{post_id}/media")
async def upload_post_media(
    post_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Upload media for a post
    """
    # Check if user is the post owner
    post = await social_service.get_post(post_id, current_user["uid"])
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    if post["userId"] != current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )
    
    media_url = await social_service.upload_post_media(post_id, file)
    if not media_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to upload media"
        )
    return {"mediaUrl": media_url}

@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Like a post
    """
    success = await social_service.like_post(post_id, current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to like post"
        )
    return {"message": "Post liked successfully"}

@router.delete("/posts/{post_id}/like")
async def unlike_post(
    post_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Unlike a post
    """
    success = await social_service.unlike_post(post_id, current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unlike post"
        )
    return {"message": "Post unliked successfully"}

@router.get("/posts/{post_id}/comments", response_model=CommentList)
async def get_post_comments(
    post_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get comments for a post
    """
    comments = await social_service.get_post_comments(
        post_id,
        current_user["uid"],
        skip=skip,
        limit=limit
    )
    return {
        "total": len(comments),
        "comments": comments
    }

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: str,
    comment_data: CommentCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new comment on a post
    """
    comment = await social_service.create_comment(post_id, current_user["uid"], comment_data)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create comment"
        )
    return comment

@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Update a comment
    """
    # Check if user is the comment owner
    comment = await social_service.get_comment(comment_id, current_user["uid"])
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment["userId"] != current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment"
        )
    
    updated_comment = await social_service.update_comment(comment_id, comment_update)
    if not updated_comment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update comment"
        )
    return updated_comment

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Delete a comment
    """
    # Check if user is the comment owner
    comment = await social_service.get_comment(comment_id, current_user["uid"])
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    if comment["userId"] != current_user["uid"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )
    
    success = await social_service.delete_comment(comment_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete comment"
        )
    return {"message": "Comment deleted successfully"}

@router.post("/comments/{comment_id}/like")
async def like_comment(
    comment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Like a comment
    """
    success = await social_service.like_comment(comment_id, current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to like comment"
        )
    return {"message": "Comment liked successfully"}

@router.delete("/comments/{comment_id}/like")
async def unlike_comment(
    comment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Unlike a comment
    """
    success = await social_service.unlike_comment(comment_id, current_user["uid"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unlike comment"
        )
    return {"message": "Comment unliked successfully"}