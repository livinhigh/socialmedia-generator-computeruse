"""
Social Media Post Generation API Endpoints.

Provides endpoints for:
1. Creating posts
2. Live WebSocket updates
3. Choosing variations
4. One-click posting (placeholder)
"""

import asyncio
import logging
from typing import Dict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session as DBSession

from socialmedia_generator.database import get_db
from socialmedia_generator.services.post_service import PostService
from socialmedia_generator.services.gemini_agent_service import GeminiAgentService
from socialmedia_generator.schemas_posts import (
    CreatePostRequest,
    CreatePostResponse,
    ChooseVariationRequest,
    ChooseVariationResponse,
    PostDetailResponse,
    WSMessageType,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Social Media Posts"])


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for live updates."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, post_id: str, websocket: WebSocket):
        """Connect a WebSocket for a specific post."""
        await websocket.accept()
        self.active_connections[post_id] = websocket
        logger.info(f"WebSocket connected for post {post_id}")

    def disconnect(self, post_id: str):
        """Disconnect WebSocket for a post."""
        if post_id in self.active_connections:
            del self.active_connections[post_id]
            logger.info(f"WebSocket disconnected for post {post_id}")

    async def send_message(self, post_id: str, message: dict):
        """Send message to WebSocket connection."""
        if post_id in self.active_connections:
            try:
                await self.active_connections[post_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {post_id}: {e}")
                self.disconnect(post_id)


manager = ConnectionManager()


# ============================================================================
# Dependency Injection
# ============================================================================

def get_post_service() -> PostService:
    """Get PostService instance."""
    return PostService()


def get_gemini_service(post_service: PostService = Depends(get_post_service)) -> GeminiAgentService:
    """Get GeminiAgentService instance."""
    return GeminiAgentService(post_service)


# ============================================================================
# Endpoint 1: Create Post
# ============================================================================

@router.post("/api/posts", response_model=CreatePostResponse)
async def create_post(
    request: CreatePostRequest,
    background_tasks: BackgroundTasks,
    post_service: PostService = Depends(get_post_service),
    db: DBSession = Depends(get_db)
):
    """
    Create a new social media post generation request.
    """
    try:
        data_sources = [
            {"type": ds.type.value, "content": ds.content}
            for ds in request.data_sources
        ]

        post = await post_service.create_post(
            db=db,
            data_sources=data_sources,
            language_tone=request.language_tone,
            media_content_needed=request.media_content_needed.value,
            text_variations_count=request.text_variations_count,
            media_variations_count=request.media_variations_count,
            content_type=request.content_type.value
        )

        if not post:
            raise HTTPException(status_code=500, detail="Failed to create post")

        return CreatePostResponse(
            post_id=post["id"],
            status=post["status"],
            message="Post created successfully. Connect to WebSocket for live updates.",
            websocket_url=f"/api/posts/{post['id']}/updates"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating post: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Endpoint 2: WebSocket Live Updates
# ============================================================================

@router.websocket("/api/posts/{post_id}/updates")
async def websocket_updates(
    websocket: WebSocket,
    post_id: str,
    db: DBSession = Depends(get_db)
):
    """
    WebSocket endpoint for live post generation updates.
    """
    post_service = PostService()
    gemini_service = GeminiAgentService(post_service)

    await manager.connect(post_id, websocket)

    #Clear all previously saved progress messages for this post and delete all text and media variations
    post_service.clear_progress_messages(db, post_id)
    post_service.delete_text_variations(db, post_id)
    post_service.delete_media_contents(db, post_id)

    try:
        await websocket.send_json({
            "type": WSMessageType.CONNECTED.value,
            "post_id": post_id,
            "message": "Connected to live updates",
            "timestamp": datetime.utcnow().isoformat()
        })

        async def progress_callback(step: str, message: str):
            await manager.send_message(post_id, {
                "type": WSMessageType.PROGRESS.value,
                "post_id": post_id,
                "step": step,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })

        success = await gemini_service.generate_post(
            db=db,
            post_id=post_id,
            progress_callback=progress_callback
        )

        if success:
            text_variations = post_service.get_text_variations(db, post_id)
            media_contents = post_service.get_media_contents(db, post_id)

            await websocket.send_json({
                "type": WSMessageType.COMPLETE.value,
                "post_id": post_id,
                "message": "Post generation completed",
                "timestamp": datetime.utcnow().isoformat(),
                "text_variation_ids": [
                    {"id": tv["id"], "variation_number": tv["variation_number"], "text_content": tv["text_content"]}
                    for tv in text_variations
                ],
                "media_content_ids": [
                    {
                        "id": mc["id"],
                        "media_type": mc["media_type"],
                        "variation_number": mc["variation_number"],
                        "file_path": mc["file_path"],
                        "generation_prompt": mc["generation_prompt"]
                    }
                    for mc in media_contents
                ]
            })
        else:
            post_data = post_service.get_post(db, post_id)
            error_msg = post_data.get("error_message", "Unknown error") if post_data else "Unknown error"
            await websocket.send_json({
                "type": WSMessageType.ERROR.value,
                "post_id": post_id,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            })

        await asyncio.sleep(2)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for post {post_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket for post {post_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": WSMessageType.ERROR.value,
                "post_id": post_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception:
            pass
    finally:
        manager.disconnect(post_id)


# ============================================================================
# Endpoint 3: Choose Variation
# ============================================================================

@router.post("/api/posts/{post_id}/select", response_model=ChooseVariationResponse)
async def choose_variation(
    post_id: str,
    request: ChooseVariationRequest,
    post_service: PostService = Depends(get_post_service),
    db: DBSession = Depends(get_db)
):
    """
    Select final variations for a post.
    """
    try:
        post = post_service.get_post(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Post is not completed yet. Current status: {post['status']}"
            )

        result = post_service.create_selection(
            db=db,
            post_id=post_id,
            text_variation_id=request.text_variation_id,
            image_ids=request.image_ids,
            video_ids=request.video_ids
        )

        if not result:
            raise HTTPException(status_code=500, detail="Failed to create selection")

        return ChooseVariationResponse(
            success=True,
            message="Variations selected successfully. Unwanted media marked for cleanup.",
            selection_id=result["selection_id"],
            unwanted_media_count=result["unwanted_media_count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error choosing variation for post {post_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Endpoint 4: One-Click Post (Placeholder)
# ============================================================================

@router.post("/api/posts/{post_id}/publish")
async def publish_post(
    post_id: str,
    db: DBSession = Depends(get_db)
):
    """
    Publish the selected post to social media platform (placeholder).
    """
    return {
        "message": "This endpoint is not yet implemented. Will be developed later.",
        "post_id": post_id,
        "status": "placeholder"
    }


# ============================================================================
# Helper Endpoint (optional) - Get Post Details
# ============================================================================

@router.get("/api/posts/{post_id}", response_model=PostDetailResponse)
async def get_post(
    post_id: str,
    post_service: PostService = Depends(get_post_service),
    db: DBSession = Depends(get_db)
):
    post = post_service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
