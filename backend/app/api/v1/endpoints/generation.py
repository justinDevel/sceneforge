"""
Scene generation API endpoints.
"""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AgentError, BriaAPIError, GenerationError
from app.core.logging import get_logger
from app.database import get_db
from app.models.schemas import FrameParams, Genre
from app.models.database import GenerationJob, Project, Frame
from app.models.schemas import GenerationStatus
from app.models.schemas import (
    ErrorResponse,
    GenerationJob as GenerationJobSchema,
    GenerationProgress,
    SceneGenerationRequest,
    SceneProject,
    SceneRefinementRequest,
)
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/generate",
    response_model=GenerationJobSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate storyboard from scene description",
    description="Start background generation of professional storyboard frames from scene description",
)
async def generate_scene(
    request: SceneGenerationRequest,
    db: Session = Depends(get_db),
) -> GenerationJobSchema:
    """
    Generate a complete storyboard from scene description.
    
    This endpoint starts a background job that uses AI agents to:
    1. Break down the scene into individual shots
    2. Convert shots to technical parameters
    3. Generate professional HDR images using Bria FIBO
    4. Ensure consistency across all frames
    
    Returns immediately with a job ID for tracking progress.
    """
    try:
        # Create project
        project_id = str(uuid4())
        print(f"Request schema:: {request}")

       
        project = Project(
            id=project_id,
            name=f"Scene: {request.scene_description[:50]}...",
            description=request.scene_description,
            genre=request.genre,
        )
        db.add(project)
        
        # Create generation job
        job_id = str(uuid4())
        job = GenerationJob(
            id=job_id,
            project_id=project_id,
            scene_description=request.scene_description,
            frame_count=request.frame_count or settings.DEFAULT_FRAME_COUNT,
            base_params=request.base_params.dict() if request.base_params else {},
        )
        db.add(job)
        db.commit()
        
        # Run the professional generation process using AI agents
        try:
            # Update job status
            job.status = GenerationStatus.PROCESSING
            job.started_at = datetime.utcnow()
            job.progress_step = 1
            job.progress_total = 4
            job.progress_message = "Starting professional generation..."
            db.commit()
            
            # Use the professional generation service with AI agents
            from app.services.generation_service import GenerationService
            generation_service = GenerationService()
            
            # Create progress callback to update job progress
            async def progress_callback(progress: Dict[str, Any]) -> None:
                job.progress_step = progress.get("step", 0)
                job.progress_total = progress.get("total_steps", 4)
                job.progress_message = progress.get("message", "Processing...")
                db.commit()
            
            # Generate professional storyboard using AI agents
            result = await generation_service.generate_storyboard(
                scene_description=request.scene_description,
                genre=request.genre,
                frame_count=request.frame_count or settings.DEFAULT_FRAME_COUNT,
                base_params=request.base_params,
                progress_callback=progress_callback,
            )
            
            print(f"Ai Agents Generation Result:: {result}")
            # Save the generated frames to the database
            await generation_service.save_frames_to_project(
                project_id,
                result["frames"],
                db
            )
            
            # Complete the job
            job.status = GenerationStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.progress_step = job.progress_total
            job.progress_message = "Professional storyboard generation completed!"
            db.commit()
            
            logger.info(
                "Professional generation completed successfully",
                job_id=job_id,
                frames_created=len(result["frames"]),
                generation_time=result["metadata"]["generation_time"]
            )
            
        except Exception as e:
            logger.error("Generation failed", error=str(e))
            job.status = GenerationStatus.FAILED
            job.error_message = str(e)
            job.progress_message = f"Generation failed: {str(e)}"
            db.commit()
        
        logger.info(
            "Generation job started",
            job_id=job_id,
            project_id=project_id,
            scene_length=len(request.scene_description),
            frame_count=request.frame_count,
        )
        
        # Manually create response to avoid serialization issues
        return {
            "id": job.id,
            "project_id": job.project_id,
            "status": job.status.value,
            "progress_step": job.progress_step or 0,
            "progress_total": job.progress_total or 1,
            "progress_message": job.progress_message,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }
        
    except Exception as e:
        logger.error("Failed to start generation job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start generation: {str(e)}",
        )


@router.get(
    "/jobs/{job_id}",
    response_model=GenerationJobSchema,
    summary="Get generation job status",
    description="Get current status and progress of a generation job",
)
async def get_generation_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> GenerationJobSchema:
    """Get generation job status and progress."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found",
        )
    
    return GenerationJobSchema.from_orm(job)


@router.get(
    "/jobs/{job_id}/progress",
    summary="Stream generation progress",
    description="Server-sent events stream of generation progress updates",
)
async def stream_generation_progress(
    job_id: str,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream real-time generation progress updates."""
    
    async def generate_progress_events():
        """Generate SSE events for progress updates."""
        last_step = 0
        
        while True:
            try:
                # Get current job status
                job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
                
                if not job:
                    yield f"event: error\ndata: Job not found\n\n"
                    break
                
                # Send progress update if changed
                if job.progress_step > last_step or job.status.value in ["completed", "failed"]:
                    progress_data = {
                        "step": job.progress_step,
                        "total_steps": job.progress_total,
                        "message": job.progress_message or "",
                        "status": job.status.value,
                        "is_complete": job.status.value in ["completed", "failed"],
                    }
                    
                    yield f"event: progress\ndata: {progress_data}\n\n"
                    last_step = job.progress_step
                
                # Break if job is complete
                if job.status.value in ["completed", "failed"]:
                    break
                
                # Wait before next check
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error("Progress streaming error", job_id=job_id, error=str(e))
                yield f"event: error\ndata: {str(e)}\n\n"
                break
    
    return StreamingResponse(
        generate_progress_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post(
    "/refine",
    response_model=GenerationJobSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Refine existing storyboard",
    description="Apply user feedback to refine existing storyboard frames",
)
async def refine_storyboard(
    request: SceneRefinementRequest,
    db: Session = Depends(get_db),
) -> GenerationJobSchema:
    """
    Refine existing storyboard based on user feedback.
    
    Uses the RefinementAgent to interpret feedback and make
    targeted improvements while maintaining consistency.
    """
    try:
        # Find the frame and project
        frame = db.query(Frame).filter(Frame.id == request.frame_id).first()
        if not frame:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Frame not found",
            )
        
        project = frame.project
        
        # Create refinement job
        job_id = str(uuid4())
        job = GenerationJob(
            id=job_id,
            project_id=project.id,
            scene_description=f"Refinement: {request.refinement_prompt}",
            frame_count=1,  # Single frame refinement
            base_params=request.params.dict() if request.params else frame.params,
        )
        db.add(job)
        db.commit()
        
        # Process refinement
        try:
            job.status = GenerationStatus.PROCESSING
            job.started_at = datetime.utcnow()
            db.commit()
            
            from app.services.generation_service import GenerationService
            generation_service = GenerationService()
            
            # Refine the frame
            result = await generation_service.refine_frame(
                frame_id=request.frame_id,
                refinement_prompt=request.refinement_prompt,
                params=request.params,
                db=db,
            )
            
            job.status = GenerationStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            logger.error("Refinement failed", error=str(e))
            job.status = GenerationStatus.FAILED
            job.error_message = str(e)
            db.commit()
        
        logger.info(
            "Refinement job started",
            job_id=job_id,
            frame_id=request.frame_id,
            refinement_length=len(request.refinement_prompt),
        )
        
        # Manually create response to avoid serialization issues
        return {
            "id": job.id,
            "project_id": job.project_id,
            "status": job.status.value,
            "progress_step": job.progress_step or 0,
            "progress_total": job.progress_total or 1,
            "progress_message": job.progress_message,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to start refinement job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start refinement: {str(e)}",
        )


@router.get(
    "/projects/{project_id}",
    summary="Get project with frames",
    description="Get complete project data including all generated frames",
)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get project with all frames."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # Query frames separately to ensure they're loaded properly
    frames = db.query(Frame).filter(Frame.project_id == project_id).order_by(Frame.sequence_number).all()
    
    # Manually construct the response to avoid Pydantic issues
    frames_data = []
    for frame in frames:
        # Ensure params is properly serialized
        params = frame.params if frame.params else {}
        frames_data.append({
            "id": frame.id,
            "image_url": frame.image_url,
            "prompt": frame.prompt,
            "params": params,
            "created_at": frame.created_at.isoformat(),
            "notes": frame.notes,
            "sequence_number": frame.sequence_number
        })
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "genre": project.genre.value,
        "status": project.status.value,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "frames": frames_data
    }



@router.post(
    "/surprise-me",
    summary="Generate creative scene suggestion",
    description="Use Gemini AI to generate creative scene descriptions and parameters",
)
async def surprise_me(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Generate creative scene suggestion using Gemini AI."""
    try:
        from app.services.surprise_service import SurpriseService
        
        surprise_service = SurpriseService()
        
        current_genre = request.get("current_genre", "noir")
        style_preference = request.get("style_preference", "cinematic")
        
        # Generate creative suggestion using Gemini
        suggestion = await surprise_service.generate_creative_scene(
            current_genre=current_genre,
            style_preference=style_preference
        )
        
        logger.info(
            "Creative scene suggestion generated",
            genre=suggestion.get("genre"),
            scene_length=len(suggestion.get("scene_description", "")),
        )
        
        return suggestion
        
    except Exception as e:
        logger.error("Failed to generate creative suggestion", error=str(e))
        
        # Fallback to predefined creative scenes
        fallback_scenes = {
            "noir": {
                "scene_description": "A rain-soaked detective follows mysterious footprints through neon-lit alleyways, shadows dancing between flickering streetlights as thunder rumbles overhead",
                "genre": "noir",
                "suggested_params": {
                    "fov": 35,
                    "lighting": 25,
                    "hdrBloom": 45,
                    "colorTemp": 3200,
                    "contrast": 75,
                    "cameraAngle": "low-angle",
                    "composition": "leading-lines"
                }
            },
            "scifi": {
                "scene_description": "A lone astronaut discovers an ancient alien artifact pulsing with ethereal energy on a desolate planet beneath twin purple moons",
                "genre": "scifi",
                "suggested_params": {
                    "fov": 24,
                    "lighting": 60,
                    "hdrBloom": 80,
                    "colorTemp": 6500,
                    "contrast": 65,
                    "cameraAngle": "eye-level",
                    "composition": "rule-of-thirds"
                }
            }
        }
        
        return fallback_scenes.get(current_genre, fallback_scenes["noir"])


@router.post(
    "/export/{project_id}",
    summary="Export project in various formats",
    description="Export storyboard project as MP4, EXR sequence, Nuke script, or JSON",
)
async def export_project(
    project_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Any:
    """Export project in specified format."""
    try:
        from app.services.export_service import ExportService
        
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Get frames
        frames = db.query(Frame).filter(Frame.project_id == project_id).order_by(Frame.sequence_number).all()
        if not frames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No frames to export",
            )
        
        export_service = ExportService()
        export_format = request.get("format", "json")
        export_options = request.get("options", {})
        
        # Generate export
        export_result = await export_service.export_project(
            project=project,
            frames=frames,
            format=export_format,
            options=export_options
        )
        
        logger.info(
            "Project exported successfully",
            project_id=project_id,
            format=export_format,
            file_size=len(export_result["content"]) if isinstance(export_result["content"], bytes) else 0
        )
        
        # Return file response
        from fastapi.responses import Response
        
        return Response(
            content=export_result["content"],
            media_type=export_result["media_type"],
            headers={
                "Content-Disposition": f"attachment; filename={export_result['filename']}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Export failed", project_id=project_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        )


@router.post(
    "/share/{project_id}",
    summary="Create shareable link for project",
    description="Generate a public shareable link for the storyboard project",
)
async def create_share_link(
    project_id: str,
    request: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Create shareable link for project."""
    try:
        from app.models.database import ShareLink
        
        # Get project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Generate share token
        import secrets
        share_token = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_in_days = request.get("expires_in_days", 30)
        allow_public_view = request.get("allow_public_view", True)
        expires_at = datetime.utcnow() + __import__('datetime').timedelta(days=expires_in_days)
        
        # Store share link in database
        share_link = ShareLink(
            id=str(uuid4()),
            project_id=project_id,
            share_token=share_token,
            expires_at=expires_at,
            allow_public_view=allow_public_view,
        )
        db.add(share_link)
        db.commit()
        
        logger.info(
            "Share link created and stored",
            project_id=project_id,
            share_token=share_token[:8] + "...",
            expires_in_days=expires_in_days
        )
        
        return {
            "share_token": share_token,
            "project_id": project_id,
            "expires_in_days": expires_in_days,
            "allow_public_view": allow_public_view,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create share link", project_id=project_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create share link: {str(e)}",
        )


@router.get(
    "/share/{share_token}",
    summary="Get project by share token",
    description="Load a shared project using its share token",
)
async def get_shared_project(
    share_token: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Get project by share token."""
    try:
        from app.models.database import ShareLink
        
        # Find share link
        share_link = db.query(ShareLink).filter(ShareLink.share_token == share_token).first()
        
        if not share_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found",
            )
        
        # Check if expired
        if share_link.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Share link has expired",
            )
        
        # Check if public view is allowed
        if not share_link.allow_public_view:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This share link is not publicly accessible",
            )
        
        # Update view count
        share_link.view_count += 1
        share_link.last_viewed_at = datetime.utcnow()
        db.commit()
        
        # Get project
        project = db.query(Project).filter(Project.id == share_link.project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        
        # Get frames
        frames = db.query(Frame).filter(Frame.project_id == project.id).order_by(Frame.sequence_number).all()
        
        # Build response
        frames_data = []
        for frame in frames:
            params = frame.params if frame.params else {}
            frames_data.append({
                "id": frame.id,
                "image_url": frame.image_url,
                "prompt": frame.prompt,
                "params": params,
                "created_at": frame.created_at.isoformat(),
                "notes": frame.notes,
                "sequence_number": frame.sequence_number
            })
        
        logger.info(
            "Shared project accessed",
            share_token=share_token[:8] + "...",
            project_id=project.id,
            view_count=share_link.view_count
        )
        
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "genre": project.genre.value,
            "status": project.status.value,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "frames": frames_data,
            "is_shared": True,
            "share_info": {
                "view_count": share_link.view_count,
                "expires_at": share_link.expires_at.isoformat(),
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get shared project", share_token=share_token[:8], error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load shared project: {str(e)}",
        )


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel generation job",
    description="Cancel a running generation job",
)
async def cancel_generation_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Cancel a running generation job."""
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found",
        )
    
    if job.status.value in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed job",
        )
    
    # Update job status
    job.status = GenerationStatus.CANCELLED
    db.commit()
    
    logger.info("Generation job cancelled", job_id=job_id)


# Background task functions

async def _run_generation_job(job_id: str, request_data: Dict[str, Any]) -> None:
    """Run generation job in background."""
    from app.database import SessionLocal
    from app.services.generation_service import GenerationService
    
    db = SessionLocal()
    generation_service = GenerationService()
    
    try:
        # Get job
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            logger.error("Generation job not found", job_id=job_id)
            return
        
        # Update job status
        job.status = GenerationStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Progress callback
        async def progress_callback(progress: Dict[str, Any]) -> None:
            job.progress_step = progress.get("step", 0)
            job.progress_total = progress.get("total_steps", 4)
            job.progress_message = progress.get("message", "")
            db.commit()
        
        # Run generation
        result = await generation_service.generate_storyboard(
            scene_description=request_data["scene_description"],
            genre=Genre(request_data["genre"]),
            frame_count=request_data.get("frame_count", 6),
            base_params=FrameParams(**request_data.get("base_params", {})),
            progress_callback=progress_callback,
        )
        
        # Save frames to database
        await generation_service.save_frames_to_project(
            job.project_id,
            result["frames"],
            db
        )
        
        # Update job completion
        job.status = GenerationStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(
            "Generation job completed",
            job_id=job_id,
            frames_generated=len(result["frames"]),
        )
        
    except Exception as e:
        logger.error("Generation job failed", job_id=job_id, error=str(e))
        
        # Update job with error
        job.status = GenerationStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()


async def _run_refinement_job(
    job_id: str,
    frame_id: str,
    refinement_prompt: str,
    params: Optional[Dict[str, Any]] = None,
) -> None:
    """Run refinement job in background."""
    from app.database import SessionLocal
    from app.services.generation_service import GenerationService
    
    db = SessionLocal()
    generation_service = GenerationService()
    
    try:
        # Get job and frame
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        frame = db.query(Frame).filter(Frame.id == frame_id).first()
        
        if not job or not frame:
            logger.error("Job or frame not found", job_id=job_id, frame_id=frame_id)
            return
        
        # Update job status
        job.status = GenerationStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Run refinement
        refined_frame = await generation_service.refine_frame(
            frame_id=frame_id,
            refinement_prompt=refinement_prompt,
            params=FrameParams(**params) if params else None,
        )
        
        # Update job completion
        job.status = GenerationStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info("Refinement job completed", job_id=job_id, frame_id=frame_id)
        
    except Exception as e:
        logger.error("Refinement job failed", job_id=job_id, error=str(e))
        
        # Update job with error
        job.status = GenerationStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()
        
    finally:
        db.close()