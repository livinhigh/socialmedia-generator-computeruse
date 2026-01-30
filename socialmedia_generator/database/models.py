"""
Database models for Computer Use Demo using SQLAlchemy.

Supports session management, task tracking, and execution history.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SessionStatus(str, Enum):
    """Session lifecycle states."""
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """Task execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Session(Base):
    """
    Represents a user session managing multiple tasks.
    
    A session is a container for related agent tasks with shared configuration,
    state, and execution context.
    """
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # Future: user tracking
    
    # Configuration
    provider = Column(String(50), default="anthropic")
    model = Column(String(100), default="claude-sonnet-4-5-20250929")
    max_output_tokens = Column(Integer, default=4096)
    enable_thinking = Column(Boolean, default=True)
    
    # State
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.CREATED, index=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # VNC Configuration
    vnc_host = Column(String(255), default="localhost")
    vnc_port = Column(Integer, default=5900)
    vnc_enabled = Column(Boolean, default=False)
    display_num = Column(Integer, nullable=True)  # X11 display number
    sibling_container_id = Column(String(255), nullable=True)  # Docker container ID for VNC display
    
    # Relationships
    tasks = relationship("Task", back_populates="session", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id={self.id}, status={self.status})>"


class Task(Base):
    """
    Represents a single task within a session.
    
    Each task is an independent agent execution with its own state,
    iterations, and results.
    """
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), index=True)
    
    # Task details
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    
    # Execution metrics
    iterations = Column(Integer, default=0)
    max_iterations = Column(Integer, default=10)
    
    # Results
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="tasks")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, status={self.status})>"


class ExecutionLog(Base):
    """
    High-level execution log for a session.
    
    Tracks session-wide events and state transitions.
    """
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), index=True)
    
    # Log details
    level = Column(String(20), default="INFO")  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session = relationship("Session", back_populates="logs")
    
    def __repr__(self):
        return f"<ExecutionLog(id={self.id}, level={self.level})>"


class TaskLog(Base):
    """
    Detailed task execution log.
    
    Tracks individual task iterations, tool calls, and progress.
    """
    __tablename__ = "task_logs"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), index=True)
    
    # Iteration info
    iteration = Column(Integer)
    
    # Log details
    content = Column(Text, nullable=False)
    log_type = Column(String(50))  # tool_use, text_response, error, etc.
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    task = relationship("Task", back_populates="logs")
    
    def __repr__(self):
        return f"<TaskLog(id={self.id}, iteration={self.iteration})>"
