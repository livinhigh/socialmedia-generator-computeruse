"""
Pydantic models for request/response validation.
"""

from typing import Optional
from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    """Request to create a new session."""
    user_id: Optional[str] = None
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-5-20250929"
    max_output_tokens: int = 4096
    enable_thinking: bool = True
    vnc_enabled: bool = False
    vnc_host: str = "localhost"


class SessionResponse(BaseModel):
    """Response model for session data."""
    id: str
    user_id: Optional[str]
    provider: str
    model: str
    max_output_tokens: int
    enable_thinking: bool
    status: str
    vnc_enabled: bool
    vnc_host: str
    vnc_port: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    task_count: int


class TaskCreateRequest(BaseModel):
    """Request to create a task."""
    description: str
    max_iterations: int = 10
    display_num: int = 1


class TaskResponse(BaseModel):
    """Response model for task data."""
    id: str
    session_id: str
    description: str
    status: str
    iterations: int
    max_iterations: int
    result: Optional[str]
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
