"""
SQLAlchemy database models for SceneForge.
Production-ready database schema with proper relationships and indexes.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func

from app.models.schemas import GenerationStatus, Genre

Base = declarative_base()


class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class Project(Base, TimestampMixin):
    """Scene project database model."""
    __tablename__ = "projects"
    
    id: Mapped[str] = Column(String(36), primary_key=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[str] = Column(Text, nullable=False)
    genre: Mapped[Genre] = Column(Enum(Genre), nullable=False)
    status: Mapped[GenerationStatus] = Column(
        Enum(GenerationStatus), 
        default=GenerationStatus.PENDING,
        nullable=False
    )
    
    # User association (for future multi-user support)
    user_id: Mapped[Optional[str]] = Column(String(36), nullable=True)
    
    # Relationships
    frames: Mapped[List["Frame"]] = relationship(
        "Frame", 
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Frame.sequence_number"
    )
    generation_jobs: Mapped[List["GenerationJob"]] = relationship(
        "GenerationJob",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
        Index("ix_projects_status", "status"),
        Index("ix_projects_genre", "genre"),
        Index("ix_projects_created_at", "created_at"),
    )


class Frame(Base, TimestampMixin):
    """Frame database model."""
    __tablename__ = "frames"
    
    id: Mapped[str] = Column(String(36), primary_key=True)
    project_id: Mapped[str] = Column(
        String(36), 
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    sequence_number: Mapped[int] = Column(Integer, nullable=False)
    
    # Content
    prompt: Mapped[str] = Column(Text, nullable=False)
    image_url: Mapped[str] = Column(String(500), nullable=False)
    notes: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # Generation parameters (stored as JSON)
    params: Mapped[dict] = Column(JSON, nullable=False)
    
    # Metadata
    generation_time: Mapped[Optional[float]] = Column(Integer, nullable=True)  # seconds
    file_size: Mapped[Optional[int]] = Column(Integer, nullable=True)  # bytes
    image_format: Mapped[Optional[str]] = Column(String(10), nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="frames")
    
    # Indexes
    __table_args__ = (
        Index("ix_frames_project_id", "project_id"),
        Index("ix_frames_sequence", "project_id", "sequence_number"),
        Index("ix_frames_created_at", "created_at"),
    )


class GenerationJob(Base, TimestampMixin):
    """Background generation job model."""
    __tablename__ = "generation_jobs"
    
    id: Mapped[str] = Column(String(36), primary_key=True)
    project_id: Mapped[str] = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Job details
    status: Mapped[GenerationStatus] = Column(
        Enum(GenerationStatus),
        default=GenerationStatus.PENDING,
        nullable=False
    )
    progress_step: Mapped[int] = Column(Integer, default=0, nullable=False)
    progress_total: Mapped[int] = Column(Integer, default=1, nullable=False)
    progress_message: Mapped[Optional[str]] = Column(String(200), nullable=True)
    
    # Request data
    scene_description: Mapped[str] = Column(Text, nullable=False)
    frame_count: Mapped[int] = Column(Integer, nullable=False)
    base_params: Mapped[dict] = Column(JSON, nullable=False)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = Column(Text, nullable=True)
    retry_count: Mapped[int] = Column(Integer, default=0, nullable=False)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="generation_jobs")
    
    # Indexes
    __table_args__ = (
        Index("ix_generation_jobs_project_id", "project_id"),
        Index("ix_generation_jobs_status", "status"),
        Index("ix_generation_jobs_created_at", "created_at"),
    )


class ExportJob(Base, TimestampMixin):
    """Export job model."""
    __tablename__ = "export_jobs"
    
    id: Mapped[str] = Column(String(36), primary_key=True)
    project_id: Mapped[str] = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Export details
    format: Mapped[str] = Column(String(20), nullable=False)
    options: Mapped[dict] = Column(JSON, nullable=False, default=dict)
    status: Mapped[GenerationStatus] = Column(
        Enum(GenerationStatus),
        default=GenerationStatus.PENDING,
        nullable=False
    )
    
    # File details
    file_path: Mapped[Optional[str]] = Column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = Column(Integer, nullable=True)
    download_url: Mapped[Optional[str]] = Column(String(500), nullable=True)
    expires_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("ix_export_jobs_project_id", "project_id"),
        Index("ix_export_jobs_status", "status"),
        Index("ix_export_jobs_expires_at", "expires_at"),
    )


class APIKey(Base, TimestampMixin):
    """API key model for authentication."""
    __tablename__ = "api_keys"
    
    id: Mapped[str] = Column(String(36), primary_key=True)
    key_hash: Mapped[str] = Column(String(128), nullable=False, unique=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    
    # User association
    user_id: Mapped[Optional[str]] = Column(String(36), nullable=True)
    
    # Permissions and limits
    is_active: Mapped[bool] = Column(Boolean, default=True, nullable=False)
    rate_limit: Mapped[int] = Column(Integer, default=60, nullable=False)  # per minute
    
    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = Column(Integer, default=0, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index("ix_api_keys_key_hash", "key_hash"),
        Index("ix_api_keys_user_id", "user_id"),
        Index("ix_api_keys_is_active", "is_active"),
    )



class ShareLink(Base, TimestampMixin):
    """Share link model for project sharing."""
    __tablename__ = "share_links"
    
    id: Mapped[str] = Column(String(36), primary_key=True)
    project_id: Mapped[str] = Column(
        String(36),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Share token (URL-safe)
    share_token: Mapped[str] = Column(String(64), unique=True, nullable=False)
    
    # Access control
    allow_public_view: Mapped[bool] = Column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = Column(DateTime(timezone=True), nullable=False)
    
    # Usage tracking
    view_count: Mapped[int] = Column(Integer, default=0, nullable=False)
    last_viewed_at: Mapped[Optional[datetime]] = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project")
    
    # Indexes
    __table_args__ = (
        Index("ix_share_links_share_token", "share_token"),
        Index("ix_share_links_project_id", "project_id"),
        Index("ix_share_links_expires_at", "expires_at"),
    )
