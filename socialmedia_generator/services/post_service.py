"""
Post Service - Manages social media post creation and variations.

Handles database operations for posts, data sources, text variations,
media content, and user selections.
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError

from socialmedia_generator.database.post_models import (
    Post, DataSource, TextVariation, MediaContent, PostSelection,
    SelectedMedia, UnwantedMedia, DataSourceType, MediaType, PostStatus, ContentType
)

logger = logging.getLogger(__name__)


class PostService:
    """
    Service for managing social media posts.
    
    Provides CRUD operations and business logic for post generation workflow.
    """
    
    def __init__(self):
        pass

    
    async def create_post(
        self,
        db: DBSession,
        data_sources: List[Dict[str, str]],
        language_tone: str,
        media_content_needed: str,
        content_type: str,
        text_variations_count: Optional[int] = 3,
        media_variations_count: Optional[int] = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new post with data sources.
        
        Args:
            db: Database session
            data_sources: List of data source dicts with 'type' and 'content'
            language_tone: Language and tone description
            media_content_needed: Type of media needed (image/video/both/none)
            content_type: Type of content (LongForm or ShortForm)
            text_variations_count: Number of text variations to generate
            media_variations_count: Number of media variations to generate
        
        Returns:
            Dict with post data or None if failed
        """
        try:
            post_id = str(uuid.uuid4())
            
            # Create post with session details
            post = Post(
                id=post_id,
                language_tone=language_tone,
                media_content_needed=MediaType(media_content_needed),
                content_type=ContentType(content_type),
                text_variations_count=text_variations_count,
                media_variations_count=media_variations_count,
                status=PostStatus.PENDING,
            )
            db.add(post)
            
            # Create data sources
            for source in data_sources:
                data_source = DataSource(
                    id=str(uuid.uuid4()),
                    post_id=post.id,
                    source_type=DataSourceType(source['type']),
                    content=source['content'],
                    is_valid=False  # Will be validated later
                )
                db.add(data_source)
            
            db.commit()
            db.refresh(post)
            
            return self._post_to_dict(post)
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating post: {e}")
            db.rollback()
            return None
    
    def get_post(self, db: DBSession, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post by ID."""
        try:
            post = db.query(Post).filter(Post.id == post_id).first()
            if not post:
                return None
            return self._post_to_dict(post, include_relations=True)
        except SQLAlchemyError as e:
            logger.error(f"Error getting post: {e}")
            return None
    
    def clear_progress_messages(self, db: DBSession, post_id: str) -> None:
        """Clear progress messages for a post."""
        try:
            post = db.query(Post).filter(Post.id == post_id).first()
            if post:
                post.current_step = None
                db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error clearing progress messages: {e}")
            db.rollback()

    def delete_text_variations(self, db: DBSession, post_id: str) -> None:
        """Delete all text variations for a post."""
        try:
            db.query(TextVariation).filter(TextVariation.post_id == post_id).delete()
            db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting text variations: {e}")
            db.rollback()
    
    def delete_media_contents(self, db: DBSession, post_id: str) -> None:
        """Delete all media contents for a post."""
        try:
            db.query(MediaContent).filter(MediaContent.post_id == post_id).delete()
            db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting media contents: {e}")
            db.rollback()

    def update_post_status(
        self,
        db: DBSession,
        post_id: str,
        status: PostStatus,
        current_step: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update post status and current step."""
        try:
            post = db.query(Post).filter(Post.id == post_id).first()
            if not post:
                return False
            
            post.status = status
            if current_step is not None:
                post.current_step = current_step
            if error_message is not None:
                post.error_message = error_message
            
            if status == PostStatus.PROCESSING_CONTEXT and not post.started_at:
                post.started_at = datetime.utcnow()
            elif status in [PostStatus.COMPLETED, PostStatus.FAILED]:
                post.completed_at = datetime.utcnow()
            
            db.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Error updating post status: {e}")
            db.rollback()
            return False
    
    def add_text_variation(
        self,
        db: DBSession,
        post_id: str,
        variation_number: int,
        text_content: str,
        image_generation_prompts: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Add a text variation to a post.
        
        Returns:
            Text variation ID or None if failed
        """
        try:
            text_var = TextVariation(
                id=str(uuid.uuid4()),
                post_id=post_id,
                variation_number=variation_number,
                text_content=text_content,
                image_generation_prompts=image_generation_prompts
            )
            db.add(text_var)
            db.commit()
            return str(text_var.id)
            
        except SQLAlchemyError as e:
            logger.error(f"Error adding text variation: {e}")
            db.rollback()
            return None
    
    def add_media_content(
        self,
        db: DBSession,
        post_id: str,
        media_type: str,
        variation_number: int,
        file_path: Optional[str] = None,
        generation_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Add media content to a post.
        
        Returns:
            Media content ID or None if failed
        """
        try:
            media = MediaContent(
                id=str(uuid.uuid4()),
                post_id=post_id,
                media_type=MediaType(media_type),
                variation_number=variation_number,
                file_path=file_path,
                generation_prompt=generation_prompt
            )
            db.add(media)
            db.commit()
            return str(media.id)
            
        except SQLAlchemyError as e:
            logger.error(f"Error adding media content: {e}")
            db.rollback()
            return None
    
    def create_selection(
        self,
        db: DBSession,
        post_id: str,
        text_variation_id: str,
        image_ids: Optional[List[str]],
        video_ids: Optional[List[str]]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a selection and mark unwanted media.
        
        Returns:
            Dict with selection info or None if failed
        """
        try:
            # Check if selection already exists
            existing = db.query(PostSelection).filter(
                PostSelection.post_id == post_id
            ).first()
            
            if existing:
                # Delete existing selection
                db.delete(existing)
                db.commit()
            
            # Create new selection
            selection = PostSelection(
                id=str(uuid.uuid4()),
                post_id=post_id,
                text_variation_id=text_variation_id
            )
            db.add(selection)
            db.flush()
            
            # Add selected media
            all_selected_ids = (image_ids or []) + (video_ids or [])
            for media_id in all_selected_ids:
                selected_media = SelectedMedia(
                    id=str(uuid.uuid4()),
                    selection_id=selection.id,
                    media_content_id=media_id
                )
                db.add(selected_media)
            
            # Mark selected items
            db.query(TextVariation).filter(
                TextVariation.id == text_variation_id
            ).update({"is_selected": True})
            
            if all_selected_ids:
                db.query(MediaContent).filter(
                    MediaContent.id.in_(all_selected_ids)
                ).update({"is_selected": True}, synchronize_session=False)
            
            # Find and mark unwanted media
            post = db.query(Post).filter(Post.id == post_id).first()
            
            unwanted_count = 0

            if post:
                all_media = db.query(MediaContent).filter(
                    MediaContent.post_id == post_id
                ).all()
                
                for media in all_media:
                    if media.id not in (all_selected_ids or []) and str(media.file_path):
                        unwanted = UnwantedMedia(
                            id=str(uuid.uuid4()),
                            media_content_id=media.id,
                            file_path=media.file_path,
                            post_id=post_id
                        )
                        db.add(unwanted)
                        unwanted_count += 1
            
            db.commit()
            
            return {
                "selection_id": selection.id,
                "unwanted_media_count": unwanted_count
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating selection: {e}")
            db.rollback()
            return None
    
    def get_data_sources(self, db: DBSession, post_id: str) -> List[Dict[str, Any]]:
        """Get all data sources for a post."""
        try:
            sources = db.query(DataSource).filter(
                DataSource.post_id == post_id
            ).all()
            return [self._data_source_to_dict(s) for s in sources]
        except SQLAlchemyError as e:
            logger.error(f"Error getting data sources: {e}")
            return []
    
    def update_data_source_validation(
        self,
        db: DBSession,
        source_id: str,
        is_valid: bool,
        extracted_text: Optional[str] = None
    ) -> bool:
        """Update data source validation status."""
        try:
            source = db.query(DataSource).filter(DataSource.id == source_id).first()
            if not source:
                return False
            
            source.is_valid = is_valid
            if extracted_text:
                source.extracted_text = extracted_text
            
            db.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Error updating data source: {e}")
            db.rollback()
            return False
    
    def get_text_variations(self, db: DBSession, post_id: str) -> List[Dict[str, Any]]:
        """Get all text variations for a post."""
        try:
            variations = db.query(TextVariation).filter(
                TextVariation.post_id == post_id
            ).order_by(TextVariation.variation_number).all()
            return [self._text_variation_to_dict(v) for v in variations]
        except SQLAlchemyError as e:
            logger.error(f"Error getting text variations: {e}")
            return []
    
    def get_media_contents(self, db: DBSession, post_id: str) -> List[Dict[str, Any]]:
        """Get all media contents for a post."""
        try:
            media = db.query(MediaContent).filter(
                MediaContent.post_id == post_id
            ).order_by(MediaContent.variation_number).all()
            return [self._media_content_to_dict(m) for m in media]
        except SQLAlchemyError as e:
            logger.error(f"Error getting media contents: {e}")
            return []
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _post_to_dict(self, post: Post, include_relations: bool = False) -> Dict[str, Any]:
        """Convert Post model to dictionary."""
        result = {
            "id": post.id,
            "language_tone": post.language_tone,
            "media_content_needed": post.media_content_needed.value,
            "content_type": post.content_type.value,
            "text_variations_count": post.text_variations_count,
            "media_variations_count": post.media_variations_count,
            "status": post.status.value,
            "current_step": post.current_step,
            "error_message": post.error_message,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "started_at": post.started_at.isoformat() if post.started_at else None,
            "completed_at": post.completed_at.isoformat() if post.completed_at else None
        }
        
        if include_relations:
            result["data_sources"] = [self._data_source_to_dict(s) for s in post.data_sources]
            result["text_variations"] = [self._text_variation_to_dict(v) for v in post.text_variations]
            result["media_contents"] = [self._media_content_to_dict(m) for m in post.media_contents]
        
        return result
    
    def _data_source_to_dict(self, source: DataSource) -> Dict[str, Any]:
        """Convert DataSource model to dictionary."""
        return {
            "id": source.id,
            "type": source.source_type.value,
            "content": source.content,
            "is_valid": source.is_valid,
            "extracted_text": source.extracted_text
        }
    
    def _text_variation_to_dict(self, variation: TextVariation) -> Dict[str, Any]:
        """Convert TextVariation model to dictionary."""
        return {
            "id": variation.id,
            "variation_number": variation.variation_number,
            "text_content": variation.text_content,
            "image_generation_prompts": variation.image_generation_prompts,
            "is_selected": variation.is_selected
        }
    
    def _media_content_to_dict(self, media: MediaContent) -> Dict[str, Any]:
        """Convert MediaContent model to dictionary."""
        return {
            "id": media.id,
            "media_type": media.media_type.value,
            "variation_number": media.variation_number,
            "file_path": media.file_path,
            "generation_prompt": media.generation_prompt,
            "is_selected": media.is_selected
        }
