from typing import Dict, List, Any, Optional
from app.db.firebase_client import get_user_by_uid
from app.config.firebase import get_firestore_client, get_auth_client
from firebase_admin import firestore, storage
import uuid
from datetime import datetime

# Collection names
POSTS_COLLECTION = "posts"
COMMENTS_COLLECTION = "comments"
LIKES_COLLECTION = "likes"
CONNECTIONS_COLLECTION = "connections"

async def get_feed(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    filter_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get posts for the user's social feed
    
    Args:
        user_id: User ID
        skip: Number of posts to skip
        limit: Maximum number of posts to return
        filter_type: Optional filter by post type
        
    Returns:
        List of posts for the feed
    """
    db = get_firestore_client()
    
    try:
        # Get user's gym ID
        user = await get_user_by_uid(user_id)
        user_gym_id = user.get("gymId") if user else None
        
        # Get user's connections
        connections_query = db.collection(CONNECTIONS_COLLECTION).where(
            "userIds", "array_contains", user_id
        ).where("status", "==", "accepted")
        
        connection_user_ids = []
        for conn in connections_query.stream():
            conn_data = conn.to_dict()
            for conn_user_id in conn_data.get("userIds", []):
                if conn_user_id != user_id:
                    connection_user_ids.append(conn_user_id)
        
        # Start with base query for all public posts
        posts_ref = db.collection(POSTS_COLLECTION).where("privacy", "==", "public")
        
        # Apply filter by post type if provided
        if filter_type:
            posts_ref = posts_ref.where("postType", "==", filter_type)
        
        # Order by creation time
        posts_ref = posts_ref.order_by("createdAt", direction=firestore.Query.DESCENDING)
        
        # Get public posts
        public_posts = []
        for post_doc in posts_ref.stream():
            post_data = post_doc.to_dict()
            post_data["id"] = post_doc.id
            
            # Check if post is already liked by the user
            like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_doc.id}_{user_id}").get()
            post_data["liked"] = like_doc.exists
            
            public_posts.append(post_data)
        
        # Get connection-only posts
        if connection_user_ids:
            connection_posts_ref = db.collection(POSTS_COLLECTION).where(
                "privacy", "==", "friends"
            ).where("userId", "in", connection_user_ids)
            
            # Apply filter by post type if provided
            if filter_type:
                connection_posts_ref = connection_posts_ref.where("postType", "==", filter_type)
            
            # Order by creation time
            connection_posts_ref = connection_posts_ref.order_by("createdAt", direction=firestore.Query.DESCENDING)
            
            for post_doc in connection_posts_ref.stream():
                post_data = post_doc.to_dict()
                post_data["id"] = post_doc.id
                
                # Check if post is already liked by the user
                like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_doc.id}_{user_id}").get()
                post_data["liked"] = like_doc.exists
                
                public_posts.append(post_data)
        
        # Get gym-only posts
        if user_gym_id:
            gym_posts_ref = db.collection(POSTS_COLLECTION).where(
                "privacy", "==", "gym"
            ).where("gymId", "==", user_gym_id)
            
            # Apply filter by post type if provided
            if filter_type:
                gym_posts_ref = gym_posts_ref.where("postType", "==", filter_type)
            
            # Order by creation time
            gym_posts_ref = gym_posts_ref.order_by("createdAt", direction=firestore.Query.DESCENDING)
            
            for post_doc in gym_posts_ref.stream():
                post_data = post_doc.to_dict()
                post_data["id"] = post_doc.id
                
                # Check if post is already liked by the user
                like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_doc.id}_{user_id}").get()
                post_data["liked"] = like_doc.exists
                
                public_posts.append(post_data)
        
        # Get the user's own private posts
        own_posts_ref = db.collection(POSTS_COLLECTION).where(
            "userId", "==", user_id
        )
        
        # Apply filter by post type if provided
        if filter_type:
            own_posts_ref = own_posts_ref.where("postType", "==", filter_type)
        
        # Order by creation time
        own_posts_ref = own_posts_ref.order_by("createdAt", direction=firestore.Query.DESCENDING)
        
        for post_doc in own_posts_ref.stream():
            post_data = post_doc.to_dict()
            
            # Skip if already added
            if any(p.get("id") == post_doc.id for p in public_posts):
                continue
                
            post_data["id"] = post_doc.id
            
            # Check if post is already liked by the user
            like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_doc.id}_{user_id}").get()
            post_data["liked"] = like_doc.exists
            
            public_posts.append(post_data)
        
        # Sort all posts by created time
        all_posts = sorted(
            public_posts,
            key=lambda x: x.get("createdAt", datetime.min),
            reverse=True
        )
        
        # Apply pagination
        paginated_posts = all_posts[skip:skip + limit]
        
        return paginated_posts
    except Exception as e:
        print(f"Error getting feed: {e}")
        return []

async def get_user_posts(
    profile_user_id: str,
    current_user_id: str,
    skip: int = 0,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get posts by a specific user
    
    Args:
        profile_user_id: User ID of the profile to view
        current_user_id: Current user's ID
        skip: Number of posts to skip
        limit: Maximum number of posts to return
        
    Returns:
        List of posts by the user
    """
    db = get_firestore_client()
    
    try:
        # Check connection status
        are_connected = False
        connection_query = db.collection(CONNECTIONS_COLLECTION).where(
            "userIds", "array_contains", current_user_id
        ).where("status", "==", "accepted")
        
        for conn in connection_query.stream():
            conn_data = conn.to_dict()
            if profile_user_id in conn_data.get("userIds", []):
                are_connected = True
                break
        
        # Check if viewing own profile
        is_own_profile = profile_user_id == current_user_id
        
        # Check if in same gym
        same_gym = False
        current_user = await get_user_by_uid(current_user_id)
        profile_user = await get_user_by_uid(profile_user_id)
        
        if current_user and profile_user:
            same_gym = current_user.get("gymId") and current_user.get("gymId") == profile_user.get("gymId")
        
        # Build query
        posts_ref = db.collection(POSTS_COLLECTION).where("userId", "==", profile_user_id)
        
        # Filter based on privacy and connection status
        if not is_own_profile:
            if are_connected:
                # Can see public and friends-only posts
                posts_ref = posts_ref.where("privacy", "in", ["public", "friends"])
            elif same_gym:
                # Can see public and gym-only posts
                posts_ref = posts_ref.where("privacy", "in", ["public", "gym"])
            else:
                # Can only see public posts
                posts_ref = posts_ref.where("privacy", "==", "public")
        
        # Order by creation time
        posts_ref = posts_ref.order_by("createdAt", direction=firestore.Query.DESCENDING)
        
        # Get posts
        posts = []
        for post_doc in posts_ref.stream():
            post_data = post_doc.to_dict()
            post_data["id"] = post_doc.id
            
            # Check if post is already liked by the user
            like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_doc.id}_{current_user_id}").get()
            post_data["liked"] = like_doc.exists
            
            posts.append(post_data)
        
        # Apply pagination
        paginated_posts = posts[skip:skip + limit]
        
        return paginated_posts
    except Exception as e:
        print(f"Error getting user posts: {e}")
        return []

async def get_gym_posts(
    gym_id: str,
    current_user_id: str,
    skip: int = 0,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get posts for a specific gym
    
    Args:
        gym_id: Gym ID
        current_user_id: Current user's ID
        skip: Number of posts to skip
        limit: Maximum number of posts to return
        
    Returns:
        List of posts for the gym
    """
    db = get_firestore_client()
    
    try:
        # Check if user is member of this gym
        current_user = await get_user_by_uid(current_user_id)
        is_member = current_user and current_user.get("gymId") == gym_id
        
        # Build query
        posts_ref = db.collection(POSTS_COLLECTION).where("gymId", "==", gym_id)
        
        # Filter based on membership
        if not is_member:
            # Only show public posts if not a member
            posts_ref = posts_ref.where("privacy", "==", "public")
        else:
            # Show public and gym-only posts if a member
            posts_ref = posts_ref.where("privacy", "in", ["public", "gym"])
        
        # Order by creation time
        posts_ref = posts_ref.order_by("createdAt", direction=firestore.Query.DESCENDING)
        
        # Get posts
        posts = []
        for post_doc in posts_ref.stream():
            post_data = post_doc.to_dict()
            post_data["id"] = post_doc.id
            
            # Check if post is already liked by the user
            like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_doc.id}_{current_user_id}").get()
            post_data["liked"] = like_doc.exists
            
            posts.append(post_data)
        
        # Apply pagination
        paginated_posts = posts[skip:skip + limit]
        
        return paginated_posts
    except Exception as e:
        print(f"Error getting gym posts: {e}")
        return []

async def create_post(user_id: str, post_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a new post
    
    Args:
        user_id: User ID
        post_data: Post data
        
    Returns:
        Created post or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Get user data
        user = await get_user_by_uid(user_id)
        if not user:
            return None
        
        # Generate unique ID for post
        post_id = str(uuid.uuid4())
        
        # Create post document
        post = {
            "userId": user_id,
            "userName": user.get("displayName", ""),
            "userPhoto": user.get("photoURL"),
            "content": post_data.get("content"),
            "privacy": post_data.get("privacy", "public"),
            "postType": post_data.get("postType", "update"),
            "media": post_data.get("media", []),
            "tags": post_data.get("tags", []),
            "location": post_data.get("location"),
            "gymId": post_data.get("gymId") or user.get("gymId"),
            "likeCount": 0,
            "commentCount": 0,
            "createdAt": firestore.SERVER_TIMESTAMP,
            "updatedAt": firestore.SERVER_TIMESTAMP
        }
        
        # Add type-specific data
        if post_data.get("postType") == "event" and post_data.get("eventData"):
            post["eventData"] = post_data.get("eventData")
        
        if post_data.get("postType") == "poll" and post_data.get("pollData"):
            post["pollData"] = post_data.get("pollData")
        
        if post_data.get("postType") == "workout" and post_data.get("workoutData"):
            post["workoutData"] = post_data.get("workoutData")
            
        if post_data.get("postType") == "achievement" and post_data.get("achievementData"):
            post["achievementData"] = post_data.get("achievementData")
        
        # Create post in Firestore
        db.collection(POSTS_COLLECTION).document(post_id).set(post)
        
        # Get created post
        created_post = db.collection(POSTS_COLLECTION).document(post_id).get()
        
        # Return post data with ID
        post_response = created_post.to_dict()
        post_response["id"] = post_id
        post_response["liked"] = False
        
        return post_response
    except Exception as e:
        print(f"Error creating post: {e}")
        return None

async def get_post(post_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific post
    
    Args:
        post_id: Post ID
        user_id: Current user's ID
        
    Returns:
        Post data or None if not found
    """
    db = get_firestore_client()
    
    try:
        post_doc = db.collection(POSTS_COLLECTION).document(post_id).get()
        if not post_doc.exists:
            return None
            
        post_data = post_doc.to_dict()
        post_data["id"] = post_id
        
        # Check privacy settings
        privacy = post_data.get("privacy")
        post_user_id = post_data.get("userId")
        post_gym_id = post_data.get("gymId")
        
        # If it's the user's own post, allow access
        if post_user_id == user_id:
            # Check if post is already liked by the user
            like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_id}_{user_id}").get()
            post_data["liked"] = like_doc.exists
            return post_data
        
        # Check privacy settings
        if privacy == "private" and post_user_id != user_id:
            return None
        
        if privacy == "friends":
            # Check if users are connected
            connection_query = db.collection(CONNECTIONS_COLLECTION).where(
                "userIds", "array_contains", user_id
            ).where("status", "==", "accepted")
            
            are_connected = False
            for conn in connection_query.stream():
                conn_data = conn.to_dict()
                if post_user_id in conn_data.get("userIds", []):
                    are_connected = True
                    break
            
            if not are_connected:
                return None
        
        if privacy == "gym":
            # Check if user is in the same gym
            current_user = await get_user_by_uid(user_id)
            if not current_user or current_user.get("gymId") != post_gym_id:
                return None
        
        # Check if post is already liked by the user
        like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_id}_{user_id}").get()
        post_data["liked"] = like_doc.exists
        
        return post_data
    except Exception as e:
        print(f"Error getting post: {e}")
        return None

async def update_post(post_id: str, post_update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a post
    
    Args:
        post_id: Post ID
        post_update: Post data to update
        
    Returns:
        Updated post or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Check if post exists
        post_doc = db.collection(POSTS_COLLECTION).document(post_id).get()
        if not post_doc.exists:
            return None
        
        # Update fields
        update_data = {"updatedAt": firestore.SERVER_TIMESTAMP}
        for key, value in post_update.items():
            if value is not None:
                update_data[key] = value
        
        # Update post
        db.collection(POSTS_COLLECTION).document(post_id).update(update_data)
        
        # Get updated post
        updated_post = db.collection(POSTS_COLLECTION).document(post_id).get()
        
        # Return updated post
        post_response = updated_post.to_dict()
        post_response["id"] = post_id
        
        # Check if post is already liked by the user
        user_id = post_response.get("userId")
        like_doc = db.collection(LIKES_COLLECTION).document(f"post_{post_id}_{user_id}").get()
        post_response["liked"] = like_doc.exists
        
        return post_response
    except Exception as e:
        print(f"Error updating post: {e}")
        return None

async def delete_post(post_id: str) -> bool:
    """
    Delete a post
    
    Args:
        post_id: Post ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if post exists
        post_doc = db.collection(POSTS_COLLECTION).document(post_id).get()
        if not post_doc.exists:
            return False
        
        # Delete all comments for this post
        comments_query = db.collection(COMMENTS_COLLECTION).where("postId", "==", post_id)
        for comment_doc in comments_query.stream():
            comment_id = comment_doc.id
            
            # Delete comment likes
            comment_likes_query = db.collection(LIKES_COLLECTION).where("targetId", "==", comment_id).where("targetType", "==", "comment")
            for like_doc in comment_likes_query.stream():
                like_doc.reference.delete()
            
            # Delete comment
            comment_doc.reference.delete()
        
        # Delete post likes
        post_likes_query = db.collection(LIKES_COLLECTION).where("targetId", "==", post_id).where("targetType", "==", "post")
        for like_doc in post_likes_query.stream():
            like_doc.reference.delete()
        
        # Delete post
        db.collection(POSTS_COLLECTION).document(post_id).delete()
        
        return True
    except Exception as e:
        print(f"Error deleting post: {e}")
        return False

async def upload_post_media(post_id: str, file) -> Optional[str]:
    """
    Upload media for a post
    
    Args:
        post_id: Post ID
        file: Uploaded file
        
    Returns:
        URL of the uploaded media or None if failed
    """
    try:
        # Check if post exists
        db = get_firestore_client()
        post_doc = db.collection(POSTS_COLLECTION).document(post_id).get()
        if not post_doc.exists:
            return None
        
        # Create a unique filename
        filename = f"posts/{post_id}/{uuid.uuid4()}-{file.filename}"
        
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
        media_url = blob.public_url
        
        # Update post media in Firestore
        post_data = post_doc.to_dict()
        current_media = post_data.get("media", [])
        current_media.append(media_url)
        
        # Update post document
        db.collection(POSTS_COLLECTION).document(post_id).update({
            "media": current_media,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return media_url
    except Exception as e:
        print(f"Error uploading post media: {e}")
        return None

async def like_post(post_id: str, user_id: str) -> bool:
    """
    Like a post
    
    Args:
        post_id: Post ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if post exists
        post_doc = db.collection(POSTS_COLLECTION).document(post_id).get()
        if not post_doc.exists:
            return False
        
        # Check if already liked
        like_id = f"post_{post_id}_{user_id}"
        like_doc = db.collection(LIKES_COLLECTION).document(like_id).get()
        if like_doc.exists:
            return True  # Already liked
        
        # Get user data
        user = await get_user_by_uid(user_id)
        if not user:
            return False
        
        # Create like document
        like_data = {
            "userId": user_id,
            "userName": user.get("displayName", ""),
            "userPhoto": user.get("photoURL"),
            "targetId": post_id,
            "targetType": "post",
            "createdAt": firestore.SERVER_TIMESTAMP
        }
        
        # Add like
        db.collection(LIKES_COLLECTION).document(like_id).set(like_data)
        
        # Increment post like count
        db.collection(POSTS_COLLECTION).document(post_id).update({
            "likeCount": firestore.Increment(1),
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return True
    except Exception as e:
        print(f"Error liking post: {e}")
        return False

async def unlike_post(post_id: str, user_id: str) -> bool:
    """
    Unlike a post
    
    Args:
        post_id: Post ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if post exists
        post_doc = db.collection(POSTS_COLLECTION).document(post_id).get()
        if not post_doc.exists:
            return False
        
        # Check if liked
        like_id = f"post_{post_id}_{user_id}"
        like_doc = db.collection(LIKES_COLLECTION).document(like_id).get()
        if not like_doc.exists:
            return True  # Already not liked
        
        # Delete like
        db.collection(LIKES_COLLECTION).document(like_id).delete()
        
        # Decrement post like count
        current_likes = post_doc.to_dict().get("likeCount", 0)
        new_like_count = max(0, current_likes - 1)  # Ensure not negative
        
        db.collection(POSTS_COLLECTION).document(post_id).update({
            "likeCount": new_like_count,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return True
    except Exception as e:
        print(f"Error unliking post: {e}")
        return False

async def get_post_comments(
    post_id: str,
    user_id: str,
    skip: int = 0,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get comments for a post
    
    Args:
        post_id: Post ID
        user_id: User ID
        skip: Number of comments to skip
        limit: Maximum number of comments to return
        
    Returns:
        List of comments for the post
    """
    db = get_firestore_client()
    
    try:
        # Check if post exists
        post_doc = db.collection(POSTS_COLLECTION).document(post_id).get()
        if not post_doc.exists:
            return []
        
        # Get comments
        comments_query = db.collection(COMMENTS_COLLECTION).where("postId", "==", post_id)
        comments_query = comments_query.order_by("createdAt", direction=firestore.Query.ASCENDING)
        
        comments = []
        for comment_doc in comments_query.stream():
            comment_data = comment_doc.to_dict()
            comment_data["id"] = comment_doc.id
            
            # Check if comment is already liked by the user
            like_doc = db.collection(LIKES_COLLECTION).document(f"comment_{comment_doc.id}_{user_id}").get()
            comment_data["liked"] = like_doc.exists
            
            comments.append(comment_data)
        
        # Apply pagination
        paginated_comments = comments[skip:skip + limit]
        
        return paginated_comments
    except Exception as e:
        print(f"Error getting post comments: {e}")
        return []

async def get_comment(comment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific comment
    
    Args:
        comment_id: Comment ID
        user_id: User ID
        
    Returns:
        Comment data or None if not found
    """
    db = get_firestore_client()
    
    try:
        comment_doc = db.collection(COMMENTS_COLLECTION).document(comment_id).get()
        if not comment_doc.exists:
            return None
            
        comment_data = comment_doc.to_dict()
        comment_data["id"] = comment_id
        
        # Check if comment is already liked by the user
        like_doc = db.collection(LIKES_COLLECTION).document(f"comment_{comment_id}_{user_id}").get()
        comment_data["liked"] = like_doc.exists
        
        return comment_data
    except Exception as e:
        print(f"Error getting comment: {e}")
        return None

async def update_comment(comment_id: str, comment_update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Update a comment
    
    Args:
        comment_id: Comment ID
        comment_update: Comment data to update
        
    Returns:
        Updated comment or None if failed
    """
    db = get_firestore_client()
    
    try:
        # Check if comment exists
        comment_doc = db.collection(COMMENTS_COLLECTION).document(comment_id).get()
        if not comment_doc.exists:
            return None
        
        # Update fields
        update_data = {"updatedAt": firestore.SERVER_TIMESTAMP}
        for key, value in comment_update.items():
            if value is not None:
                update_data[key] = value
        
        # Update comment
        db.collection(COMMENTS_COLLECTION).document(comment_id).update(update_data)
        
        # Get updated comment
        updated_comment = db.collection(COMMENTS_COLLECTION).document(comment_id).get()
        
        # Return updated comment
        comment_response = updated_comment.to_dict()
        comment_response["id"] = comment_id
        
        # Check if comment is already liked by the user
        user_id = comment_response.get("userId")
        like_doc = db.collection(LIKES_COLLECTION).document(f"comment_{comment_id}_{user_id}").get()
        comment_response["liked"] = like_doc.exists
        
        return comment_response
    except Exception as e:
        print(f"Error updating comment: {e}")
        return None

async def delete_comment(comment_id: str) -> bool:
    """
    Delete a comment
    
    Args:
        comment_id: Comment ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if comment exists
        comment_doc = db.collection(COMMENTS_COLLECTION).document(comment_id).get()
        if not comment_doc.exists:
            return False
        
        comment_data = comment_doc.to_dict()
        post_id = comment_data.get("postId")
        
        # Delete comment likes
        comment_likes_query = db.collection(LIKES_COLLECTION).where("targetId", "==", comment_id).where("targetType", "==", "comment")
        for like_doc in comment_likes_query.stream():
            like_doc.reference.delete()
        
        # Delete comment
        db.collection(COMMENTS_COLLECTION).document(comment_id).delete()
        
        # Decrement post comment count
        if post_id:
            post_doc = db.collection(POSTS_COLLECTION).document(post_id).get()
            if post_doc.exists:
                current_comments = post_doc.to_dict().get("commentCount", 0)
                new_comment_count = max(0, current_comments - 1)  # Ensure not negative
                
                db.collection(POSTS_COLLECTION).document(post_id).update({
                    "commentCount": new_comment_count,
                    "updatedAt": firestore.SERVER_TIMESTAMP
                })
        
        return True
    except Exception as e:
        print(f"Error deleting comment: {e}")
        return False

async def like_comment(comment_id: str, user_id: str) -> bool:
    """
    Like a comment
    
    Args:
        comment_id: Comment ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if comment exists
        comment_doc = db.collection(COMMENTS_COLLECTION).document(comment_id).get()
        if not comment_doc.exists:
            return False
        
        # Check if already liked
        like_id = f"comment_{comment_id}_{user_id}"
        like_doc = db.collection(LIKES_COLLECTION).document(like_id).get()
        if like_doc.exists:
            return True  # Already liked
        
        # Get user data
        user = await get_user_by_uid(user_id)
        if not user:
            return False
        
        # Create like document
        like_data = {
            "userId": user_id,
            "userName": user.get("displayName", ""),
            "userPhoto": user.get("photoURL"),
            "targetId": comment_id,
            "targetType": "comment",
            "createdAt": firestore.SERVER_TIMESTAMP
        }
        
        # Add like
        db.collection(LIKES_COLLECTION).document(like_id).set(like_data)
        
        # Increment comment like count
        db.collection(COMMENTS_COLLECTION).document(comment_id).update({
            "likeCount": firestore.Increment(1),
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return True
    except Exception as e:
        print(f"Error liking comment: {e}")
        return False

async def unlike_comment(comment_id: str, user_id: str) -> bool:
    """
    Unlike a comment
    
    Args:
        comment_id: Comment ID
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    db = get_firestore_client()
    
    try:
        # Check if comment exists
        comment_doc = db.collection(COMMENTS_COLLECTION).document(comment_id).get()
        if not comment_doc.exists:
            return False
        
        # Check if liked
        like_id = f"comment_{comment_id}_{user_id}"
        like_doc = db.collection(LIKES_COLLECTION).document(like_id).get()
        if not like_doc.exists:
            return True  # Already not liked
        
        # Delete like
        db.collection(LIKES_COLLECTION).document(like_id).delete()
        
        # Decrement comment like count
        current_likes = comment_doc.to_dict().get("likeCount", 0)
        new_like_count = max(0, current_likes - 1)  # Ensure not negative
        
        db.collection(COMMENTS_COLLECTION).document(comment_id).update({
            "likeCount": new_like_count,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        
        return True
    except Exception as e:
        print(f"Error unliking comment: {e}")
        return False