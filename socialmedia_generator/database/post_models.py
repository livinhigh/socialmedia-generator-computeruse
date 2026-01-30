"""
Database models for Social Media Post Generation.

Handles posts, text variations, media content, and user selections.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from socialmedia_generator.database.models import Base


class DataSourceType(str, Enum):
    """Type of data source."""
    TEXT = "text"
    LINK = "link"


class MediaType(str, Enum):
    """Type of media content."""
    IMAGE = "image"
    VIDEO = "video"
    BOTH = "both"
    NONE = "none"


class PostStatus(str, Enum):
    """Post generation status."""
    PENDING = "pending"
    PROCESSING_CONTEXT = "processing_context"
    GENERATING_TEXT = "generating_text"
    GENERATING_MEDIA = "generating_media"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentType(str, Enum):
    """Type of content to generate."""
    LONG_FORM = "LongForm"
    SHORT_FORM = "ShortForm"


class Post(Base):
    """
    Represents a social media post creation request.
    
    Tracks the entire lifecycle of post generation including
    data sources, configuration, and generated variations.
    """
    __tablename__ = "posts"
    
    id = Column(String(36), primary_key=True, index=True)
    
    # Request Configuration
    language_tone: Mapped[str] = mapped_column(Text, nullable=False)  # Language and tone description
    media_content_needed: Mapped[MediaType] = mapped_column(SQLEnum(MediaType), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(SQLEnum(ContentType), nullable=False)
    text_variations_count: Mapped[int] = mapped_column(Integer, default=3)
    media_variations_count: Mapped[int] = mapped_column(Integer, default=3)
    
    # Status & Tracking
    status: Mapped[PostStatus] = mapped_column(SQLEnum(PostStatus), default=PostStatus.PENDING, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_step: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Current processing step description
    
    # Session Reference (for computer-use agent)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=True, index=True)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("Session", foreign_keys=[session_id])
    data_sources = relationship("DataSource", back_populates="post", cascade="all, delete-orphan")
    text_variations = relationship("TextVariation", back_populates="post", cascade="all, delete-orphan")
    media_contents = relationship("MediaContent", back_populates="post", cascade="all, delete-orphan")
    selection = relationship("PostSelection", back_populates="post", uselist=False, cascade="all, delete-orphan")


class DataSource(Base):
    """
    Data sources for post content generation.
    
    Can be either text input or URLs that need to be scraped.
    """
    __tablename__ = "data_sources"
    
    id = Column(String(36), primary_key=True, index=True)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source_type: Mapped[DataSourceType] = mapped_column(SQLEnum(DataSourceType), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Either raw text or URL
    is_valid: Mapped[bool] = mapped_column(Boolean, default=False)  # Validation status for links
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Extracted content from links
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="data_sources")


class TextVariation(Base):
    """
    Generated text variations for social media posts.
    
    Each variation includes the text content and associated image generation prompts.
    """
    __tablename__ = "text_variations"
    
    id = Column(String(36), primary_key=True, index=True)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    variation_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, etc.
    text_content: Mapped[str] = mapped_column(Text, nullable=False)  # The actual post text
    image_generation_prompts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Tags/prompts for image generation
    
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)  # User selection flag
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="text_variations")


class MediaContent(Base):
    """
    Generated media content (images/videos) for posts.
    
    Stores paths to generated media files and their metadata.
    """
    __tablename__ = "media_contents"
    
    id = Column(String(36), primary_key=True, index=True)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    media_type: Mapped[MediaType] = mapped_column(SQLEnum(MediaType), nullable=False)
    variation_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, etc.
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Path to media file
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Prompt used to generate this media
    
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)  # User selection flag
    
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="media_contents")


class PostSelection(Base):
    """
    User's final selection of text and media variations.
    
    Tracks which variations were chosen for the final post.
    """
    __tablename__ = "post_selections"
    
    id = Column(String(36), primary_key=True, index=True)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    
    text_variation_id = Column(String(36), ForeignKey("text_variations.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("Post", back_populates="selection")
    text_variation = relationship("TextVariation")
    selected_media = relationship("SelectedMedia", back_populates="selection", cascade="all, delete-orphan")


class SelectedMedia(Base):
    """
    Individual media items selected for the final post.
    
    Links media content to the user's selection.
    """
    __tablename__ = "selected_media"
    
    id = Column(String(36), primary_key=True, index=True)
    selection_id = Column(String(36), ForeignKey("post_selections.id", ondelete="CASCADE"), nullable=False, index=True)
    media_content_id = Column(String(36), ForeignKey("media_contents.id"), nullable=False)
    
    # Relationships
    selection = relationship("PostSelection", back_populates="selected_media")
    media_content = relationship("MediaContent")


class UnwantedMedia(Base):
    """
    Media content not selected by user - to be cleaned up after 2 days.
    
    This table stores references to media files that should be deleted
    by a scheduled cleanup job.
    """
    __tablename__ = "unwanted_media"
    
    id = Column(String(36), primary_key=True, index=True)
    media_content_id = Column(String(36), nullable=False)  # Reference to original media
    file_path = Column(String(500), nullable=False)  # Path to file to be deleted
    post_id = Column(String(36), nullable=False, index=True)  # For tracking
    
    marked_at = Column(DateTime, default=datetime.utcnow, index=True)  # For cleanup job filtering
