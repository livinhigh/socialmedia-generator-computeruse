"""
Pydantic schemas for Social Media Post Generation API.

Request/response models for validation and serialization.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class DataSourceTypeEnum(str, Enum):
    """Type of data source."""
    TEXT = "text"
    LINK = "link"


class MediaTypeEnum(str, Enum):
    """Type of media content needed."""
    IMAGE = "image"
    VIDEO = "video"
    BOTH = "both"
    NONE = "none"


class PostStatusEnum(str, Enum):
    """Post generation status."""
    PENDING = "pending"
    PROCESSING_CONTEXT = "processing_context"
    GENERATING_TEXT = "generating_text"
    GENERATING_MEDIA = "generating_media"
    COMPLETED = "completed"
    FAILED = "failed"


class ContentTypeEnum(str, Enum):
    """Type of content to generate."""
    LONG_FORM = "LongForm"
    SHORT_FORM = "ShortForm"


# ============================================================================
# Request Models
# ============================================================================

class DataSourceInput(BaseModel):
    """Individual data source input."""
    type: DataSourceTypeEnum
    content: str = Field(..., min_length=1, description="Text content or URL")
    
    @validator('content')
    def validate_content(cls, v, values):
        """Validate content based on type."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        
        source_type = values.get('type')
        if source_type == DataSourceTypeEnum.LINK:
            # Basic URL validation - more thorough validation will be done server-side
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError("Link must start with http:// or https://")
        
        return v.strip()


class CreatePostRequest(BaseModel):
    """Request to create a new social media post."""
    data_sources: List[DataSourceInput] = Field(..., min_length=1, description="At least one data source required")
    language_tone: str = Field(..., min_length=1, description="Language and tone description for post")
    media_content_needed: MediaTypeEnum = Field(..., description="Type of media content needed")
    content_type: ContentTypeEnum = Field(..., description="Type of content (LongForm or ShortForm)")
    text_variations_count: Optional[int] = Field(3, ge=1, le=10, description="Number of text variations (1-10)")
    media_variations_count: Optional[int] = Field(3, ge=1, le=10, description="Number of media variations (1-10)")
    
    @validator('data_sources')
    def validate_data_sources(cls, v):
        """Ensure at least one valid data source."""
        if not v or len(v) == 0:
            raise ValueError("At least one data source is required")
        return v


class ChooseVariationRequest(BaseModel):
    """Request to select variations for final post."""
    text_variation_id: str = Field(..., description="ID of selected text variation")
    image_ids: Optional[List[str]] = Field(default=[], description="List of selected image IDs")
    video_ids: Optional[List[str]] = Field(default=[], description="List of selected video IDs")
    
    @validator('text_variation_id')
    def validate_text_id(cls, v):
        """Ensure text variation ID is provided."""
        if not v or not v.strip():
            raise ValueError("Text variation ID is required")
        return v.strip()
    
    @validator('image_ids', 'video_ids')
    def validate_media_ids(cls, v):
        """Ensure media IDs are unique if provided."""
        if v and len(v) != len(set(v)):
            raise ValueError("Duplicate media IDs are not allowed")
        return v or []


# ============================================================================
# Response Models
# ============================================================================

class DataSourceResponse(BaseModel):
    """Response model for data source."""
    id: str
    type: str
    content: str
    is_valid: bool
    
    class Config:
        from_attributes = True


class TextVariationResponse(BaseModel):
    """Response model for text variation."""
    id: str
    variation_number: int
    text_content: str
    image_generation_prompts: Optional[dict]
    is_selected: bool
    
    class Config:
        from_attributes = True


class MediaContentResponse(BaseModel):
    """Response model for media content."""
    id: str
    media_type: str
    variation_number: int
    file_path: Optional[str]
    is_selected: bool
    
    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    """Response model for post."""
    id: str
    language_tone: str
    media_content_needed: str
    text_variations_count: int
    media_variations_count: int
    status: str
    current_step: Optional[str]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    
    class Config:
        from_attributes = True


class PostDetailResponse(PostResponse):
    """Detailed response with variations."""
    data_sources: List[DataSourceResponse]
    text_variations: List[TextVariationResponse]
    media_contents: List[MediaContentResponse]


class CreatePostResponse(BaseModel):
    """Response after creating a post."""
    post_id: str
    status: str
    message: str
    websocket_url: str


class WebSocketProgressMessage(BaseModel):
    """WebSocket progress update message."""
    type: str  # "progress" or "complete"
    step: str
    message: str
    post_id: str
    status: Optional[str] = None
    # For completion message
    text_variations: Optional[List[dict]] = None
    media_contents: Optional[List[dict]] = None


class ChooseVariationResponse(BaseModel):
    """Response after selecting variations."""
    success: bool
    message: str
    selection_id: str
    unwanted_media_count: int


# ============================================================================
# WebSocket Message Types
# ============================================================================

class WSMessageType(str, Enum):
    """WebSocket message types."""
    CONNECTED = "connected"
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETE = "complete"
    DISCONNECTED = "disconnected"


class WSMessage(BaseModel):
    """Base WebSocket message structure."""
    type: WSMessageType
    post_id: str
    timestamp: str


class WSProgressMessage(WSMessage):
    """Progress update message."""
    step: str
    message: str
    status: str


class WSCompleteMessage(WSMessage):
    """Completion message with generated content IDs."""
    text_variation_ids: List[dict]  # [{"id": "...", "variation_number": 1}, ...]
    media_content_ids: List[dict]   # [{"id": "...", "media_type": "image", "variation_number": 1}, ...]


class WSErrorMessage(WSMessage):
    """Error message."""
    error: str
    step: Optional[str] = None
