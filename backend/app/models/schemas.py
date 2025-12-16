"""
Pydantic schemas for SceneForge API.
Production-ready data validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class CameraAngle(str, Enum):
    """Camera angle options."""
    EYE_LEVEL = "eye-level"
    LOW_ANGLE = "low-angle"
    HIGH_ANGLE = "high-angle"
    DUTCH_ANGLE = "dutch-angle"
    BIRDS_EYE = "birds-eye"
    WORMS_EYE = "worms-eye"
    OVER_SHOULDER = "over-shoulder"
    POV = "pov"


class Composition(str, Enum):
    """Composition rule options."""
    RULE_OF_THIRDS = "rule-of-thirds"
    CENTERED = "centered"
    SYMMETRICAL = "symmetrical"
    LEADING_LINES = "leading-lines"
    FRAME_WITHIN_FRAME = "frame-within-frame"
    NEGATIVE_SPACE = "negative-space"
    GOLDEN_RATIO = "golden-ratio"


class Genre(str, Enum):
    """Film genre options."""
    NOIR = "noir"
    SCIFI = "scifi"
    HORROR = "horror"
    ACTION = "action"
    DRAMA = "drama"
    FANTASY = "fantasy"
    THRILLER = "thriller"
    WESTERN = "western"


class GenerationStatus(str, Enum):
    """Generation status options."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FrameParams(BaseModel):
    """Frame generation parameters."""
    fov: int = Field(default=50, ge=10, le=120, description="Field of view in degrees")
    lighting: int = Field(default=60, ge=0, le=100, description="Lighting intensity")
    hdr_bloom: int = Field(default=30, ge=0, le=100, description="HDR bloom intensity")
    color_temp: int = Field(default=5500, ge=2000, le=10000, description="Color temperature in Kelvin")
    contrast: int = Field(default=50, ge=0, le=100, description="Contrast level")
    camera_angle: CameraAngle = Field(default=CameraAngle.EYE_LEVEL, description="Camera angle")
    composition: Composition = Field(default=Composition.RULE_OF_THIRDS, description="Composition rule")


class FrameCreate(BaseModel):
    """Frame creation request."""
    prompt: str = Field(..., min_length=10, max_length=1000, description="Scene description")
    params: FrameParams = Field(default_factory=FrameParams, description="Generation parameters")
    notes: Optional[str] = Field(default=None, max_length=500, description="Optional notes")


class FrameUpdate(BaseModel):
    """Frame update request."""
    prompt: Optional[str] = Field(default=None, min_length=10, max_length=1000)
    params: Optional[FrameParams] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=500)


class Frame(BaseModel):
    """Frame response model."""
    id: str = Field(..., description="Unique frame identifier")
    image_url: str = Field(..., description="Generated image URL")
    prompt: str = Field(..., description="Scene description used")
    params: FrameParams = Field(..., description="Generation parameters used")
    timestamp: datetime = Field(..., description="Creation timestamp")
    notes: Optional[str] = Field(default=None, description="Optional notes")
    
    class Config:
        from_attributes = True


class SceneGenerationRequest(BaseModel):
    """Scene generation request."""
    scene_description: str = Field(
        ..., 
        min_length=20, 
        max_length=2000, 
        description="High-level scene description"
    )
    genre: Genre = Field(..., description="Film genre")
    frame_count: Optional[int] = Field(
        default=6, 
        ge=1, 
        le=20, 
        description="Number of frames to generate"
    )
    base_params: Optional[FrameParams] = Field(
        default_factory=FrameParams, 
        description="Base parameters for all frames"
    )
    
    @validator("scene_description")
    def validate_scene_description(cls, v: str) -> str:
        """Validate scene description content."""
        if not v.strip():
            raise ValueError("Scene description cannot be empty")
        return v.strip()


class SceneRefinementRequest(BaseModel):
    """Scene refinement request."""
    frame_id: str = Field(..., description="Frame ID to refine")
    refinement_prompt: str = Field(
        ..., 
        min_length=5, 
        max_length=500, 
        description="Refinement instructions"
    )
    params: Optional[FrameParams] = Field(default=None, description="Updated parameters")


class GenerationProgress(BaseModel):
    """Generation progress update."""
    step: int = Field(..., ge=0, description="Current step number")
    total_steps: int = Field(..., ge=1, description="Total number of steps")
    message: str = Field(..., description="Current step description")
    is_complete: bool = Field(default=False, description="Whether generation is complete")
    estimated_time_remaining: Optional[int] = Field(
        default=None, 
        description="Estimated seconds remaining"
    )


class SceneProject(BaseModel):
    """Scene project model."""
    id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(..., min_length=1, max_length=1000, description="Project description")
    genre: Genre = Field(..., description="Film genre")
    frames: List[Frame] = Field(default_factory=list, description="Project frames")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    status: GenerationStatus = Field(default=GenerationStatus.PENDING, description="Project status")
    
    class Config:
        from_attributes = True


class SceneProjectCreate(BaseModel):
    """Scene project creation request."""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field(..., min_length=1, max_length=1000, description="Project description")
    genre: Genre = Field(..., description="Film genre")


class SceneProjectUpdate(BaseModel):
    """Scene project update request."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    genre: Optional[Genre] = Field(default=None)


class GenerationJob(BaseModel):
    """Background generation job."""
    id: str = Field(..., description="Unique job identifier")
    project_id: str = Field(..., description="Associated project ID")
    status: GenerationStatus = Field(..., description="Job status")
    progress_step: int = Field(default=0, description="Current progress step")
    progress_total: int = Field(default=1, description="Total progress steps")
    progress_message: Optional[str] = Field(default=None, description="Current progress message")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm to handle datetime serialization properly."""
        data = {
            "id": obj.id,
            "project_id": obj.project_id,
            "status": obj.status,
            "progress_step": obj.progress_step or 0,
            "progress_total": obj.progress_total or 1,
            "progress_message": obj.progress_message,
            "created_at": obj.created_at,
            "started_at": obj.started_at,
            "completed_at": obj.completed_at,
            "error_message": obj.error_message,
        }
        return cls(**data)


class ExportFormat(str, Enum):
    """Export format options."""
    EXR = "exr"
    PNG = "png"
    JPG = "jpg"
    MP4 = "mp4"
    NUKE_SCRIPT = "nuke"
    COMFYUI_WORKFLOW = "comfyui"


class ExportRequest(BaseModel):
    """Export request."""
    project_id: str = Field(..., description="Project ID to export")
    format: ExportFormat = Field(..., description="Export format")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Format-specific options"
    )


class ExportResponse(BaseModel):
    """Export response."""
    export_id: str = Field(..., description="Unique export identifier")
    download_url: str = Field(..., description="Download URL")
    expires_at: datetime = Field(..., description="URL expiration timestamp")
    file_size: int = Field(..., description="File size in bytes")


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy", description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Service statuses")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }