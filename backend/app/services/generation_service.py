"""
Generation service - Orchestrates the complete storyboard generation process.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.orchestrator import AgentOrchestrator
from app.core.exceptions import GenerationError
from app.core.logging import LoggerMixin
from app.models.database import Frame, Project
from app.models.schemas import FrameParams, Genre
from app.services.bria_client import BriaClient
from app.services.storage_service import StorageService


class GenerationService(LoggerMixin):
    """
    Service for orchestrating complete storyboard generation.
    
    Coordinates between:
    - AI agents for scene analysis and parameter generation
    - Bria FIBO for professional image generation
    - Storage service for file management
    - Database for persistence
    """
    
    def __init__(self) -> None:
        self.orchestrator = AgentOrchestrator()
        self.storage_service = StorageService()
    
    async def generate_storyboard(
        self,
        scene_description: str,
        genre: Genre,
        frame_count: int = 6,
        base_params: Optional[FrameParams] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete professional storyboard.
        
        Args:
            scene_description: High-level scene description
            genre: Film genre for style guidance
            frame_count: Target number of frames
            base_params: Base parameters for generation
            progress_callback: Optional progress callback
            
        Returns:
            Complete storyboard with frames and metadata
        """
        self.logger.info(
            "Starting storyboard generation",
            scene_length=len(scene_description),
            genre=genre.value,
            frame_count=frame_count,
        )
        
        try:
            # Step 1: Generate frame parameters using AI agents
            if progress_callback:
                await progress_callback({
                    "step": 1,
                    "total_steps": 6,
                    "message": "Analyzing scene with AI agents...",
                })
            
            agent_result = await self.orchestrator.generate_storyboard(
                scene_description=scene_description,
                genre=genre,
                frame_count=frame_count,
                base_params=base_params,
                progress_callback=self._create_agent_progress_callback(progress_callback, 1, 3),
            )
            
            # Step 2: Generate images using Bria FIBO
            if progress_callback:
                await progress_callback({
                    "step": 4,
                    "total_steps": 6,
                    "message": "Generating professional HDR images...",
                })
            
            frames_with_images = await self._generate_images_for_frames(
                agent_result["frames"],
                progress_callback=self._create_image_progress_callback(progress_callback, 4, 5),
            )
            
            # Step 3: Store images and finalize
            if progress_callback:
                await progress_callback({
                    "step": 6,
                    "total_steps": 6,
                    "message": "Finalizing storyboard...",
                })
            
            # Update agent result with generated images
            agent_result["frames"] = frames_with_images
            
            self.logger.info(
                "Storyboard generation completed",
                frames_generated=len(frames_with_images),
                generation_time=agent_result["metadata"]["generation_time"],
            )
            
            return agent_result
            
        except Exception as e:
            self.logger.error("Storyboard generation failed", error=str(e))
            raise GenerationError(f"Storyboard generation failed: {str(e)}")
    
    async def refine_frame(
        self,
        frame_id: str,
        refinement_prompt: str,
        params: Optional[FrameParams] = None,
        db: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Refine a specific frame based on user feedback using Bria V2 API.
        
        Args:
            frame_id: ID of frame to refine
            refinement_prompt: User feedback for refinement
            params: Optional updated parameters
            db: Database session
            
        Returns:
            Refined frame data
        """
        self.logger.info(
            "Starting frame refinement",
            frame_id=frame_id,
            refinement_length=len(refinement_prompt),
        )
        
        try:
            # Get current frame from database if db session provided
            from app.models.database import Frame as DBFrame
            current_frame = None
            if db:
                current_frame = db.query(DBFrame).filter(DBFrame.id == frame_id).first()
            
            if not current_frame:
                self.logger.warning("Frame not found in database, using default params")
                frame_params = params or FrameParams()
                original_prompt = "Scene frame"
                structured_prompt = None
            else:
                frame_params = FrameParams(**current_frame.params) if current_frame.params else (params or FrameParams())
                original_prompt = current_frame.prompt
                # Structured prompt not stored in database, will be regenerated
                structured_prompt = None
            
            # Refine image using Bria V2 API
            async with BriaClient() as bria:
                bria_response = await bria.refine_image(
                    original_prompt=original_prompt,
                    refinement_prompt=refinement_prompt,
                    params=frame_params,
                    structured_prompt=structured_prompt,
                    original_image_url=current_frame.image_url if current_frame else None,
                )
                
                if bria_response.image_url:
                    # Handle mock vs real responses
                    if bria_response.image_url == "/placeholder.svg" or not bria_response.image_url.startswith('http'):
                        stored_url = "/placeholder.svg"
                    else:
                        # Real Bria API - detect format and store
                        original_url = bria_response.image_url
                        if '.png' in original_url.lower():
                            extension = '.png'
                        elif '.jpg' in original_url.lower() or '.jpeg' in original_url.lower():
                            extension = '.jpg'
                        elif '.webp' in original_url.lower():
                            extension = '.webp'
                        else:
                            extension = '.png'
                        
                        # Store the refined image
                        stored_url = await self.storage_service.store_image_from_url(
                            bria_response.image_url,
                            f"refined_{frame_id}_{int(datetime.utcnow().timestamp())}{extension}"
                        )
                    
                    # Update frame in database if available
                    if db and current_frame:
                        current_frame.image_url = stored_url
                        current_frame.prompt = f"{original_prompt} (refined: {refinement_prompt})"
                        if params:
                            current_frame.params = params.dict()
                        db.commit()
                    
                    result = {
                        "frame_id": frame_id,
                        "image_url": stored_url,
                        "prompt": f"{original_prompt} (refined: {refinement_prompt})",
                        "parameters": frame_params.dict(),
                        "refinement_prompt": refinement_prompt,
                        "metadata": {
                            "bria_id": bria_response.id,
                            "refinement_time": datetime.utcnow().isoformat(),
                        }
                    }
                    
                    self.logger.info("Frame refinement completed", frame_id=frame_id)
                    return result
                else:
                    raise GenerationError("No image URL in refinement response")
            
        except Exception as e:
            self.logger.error("Frame refinement failed", frame_id=frame_id, error=str(e))
            raise GenerationError(f"Frame refinement failed: {str(e)}")
    
    async def save_frames_to_project(
        self,
        project_id: str,
        frames: List[Dict[str, Any]],
        db: Session,
    ) -> None:
        """
        Save generated frames to database project.
        
        Args:
            project_id: Target project ID
            frames: Generated frame data
            db: Database session
        """
        try:
            for i, frame_data in enumerate(frames):
                # Handle both mock and real frame data structures
                frame_id = frame_data.get("frame_id") or frame_data.get("id") or str(uuid4())
                prompt = frame_data.get("prompt", "Generated scene frame")
                image_url = frame_data.get("image_url", "/placeholder.svg")  # Use placeholder for mock
                
                # Handle parameters - could be nested or direct
                params = frame_data.get("parameters", frame_data.get("params", {}))
                if not params:
                    # Create default parameters if none provided
                    params = {
                        "fov": 50,
                        "lighting": 60,
                        "hdr_bloom": 30,
                        "color_temp": 5500,
                        "contrast": 50,
                        "camera_angle": "eye-level",
                        "composition": "rule-of-thirds"
                    }
                
                frame = Frame(
                    id=frame_id,
                    project_id=project_id,
                    sequence_number=i + 1,
                    prompt=prompt,
                    image_url=image_url,
                    params=params,
                    notes=frame_data.get("notes"),
                )
                db.add(frame)
            
            db.commit()
            
            self.logger.info(
                "Frames saved to project",
                project_id=project_id,
                frame_count=len(frames),
            )
            
        except Exception as e:
            db.rollback()
            self.logger.error(
                "Failed to save frames",
                project_id=project_id,
                error=str(e),
            )
            raise
    
    async def _generate_images_for_frames(
        self,
        frames: List[Dict[str, Any]],
        progress_callback: Optional[callable] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate images for all frames using Bria FIBO.
        
        Args:
            frames: Frame parameters from agents
            progress_callback: Optional progress callback
            
        Returns:
            Frames with generated image URLs
        """
        frames_with_images = []
        
        async with BriaClient() as bria:
            for i, frame_data in enumerate(frames):
                try:
                    if progress_callback:
                        await progress_callback({
                            "step": i + 1,
                            "total_steps": len(frames),
                            "message": f"Generating image {i + 1}/{len(frames)}...",
                        })
                    
                    # Convert parameters to FrameParams
                    frame_params = FrameParams(**frame_data["parameters"])
                    
                    # Generate image with Bria FIBO
                    bria_response = await bria.generate_image(
                        frame_data["prompt"],
                        frame_params,
                    )
                    
                    if bria_response.image_url:
                        # Handle mock vs real responses
                        if bria_response.image_url == "/placeholder.svg" or not bria_response.image_url.startswith('http'):
                            # Mock response - use placeholder but ensure it's accessible
                            stored_url = "/placeholder.svg"
                        else:
                            # Real Bria API - detect format from URL and store
                            original_url = bria_response.image_url
                            if '.png' in original_url.lower():
                                extension = '.png'
                            elif '.jpg' in original_url.lower() or '.jpeg' in original_url.lower():
                                extension = '.jpg'
                            elif '.webp' in original_url.lower():
                                extension = '.webp'
                            else:
                                extension = '.png'  # Default to PNG for real images
                            
                            # Store the image with correct extension
                            filename = f"frame_{frame_data['frame_id']}_{int(datetime.utcnow().timestamp())}{extension}"
                            stored_url = await self.storage_service.store_image_from_url(
                                bria_response.image_url,
                                filename
                            )
                        
                        # Update frame data
                        frame_data["image_url"] = stored_url
                        frame_data["generation_metadata"] = {
                            "bria_id": bria_response.id,
                            "generation_time": datetime.utcnow().isoformat(),
                        }
                    else:
                        self.logger.warning(
                            "No image URL in Bria response",
                            frame_id=frame_data["frame_id"],
                        )
                        frame_data["image_url"] = ""
                    
                    frames_with_images.append(frame_data)
                    
                except Exception as e:
                    self.logger.error(
                        "Failed to generate image for frame",
                        frame_id=frame_data.get("frame_id", "unknown"),
                        error=str(e),
                    )
                    # Add frame without image
                    frame_data["image_url"] = ""
                    frame_data["generation_error"] = str(e)
                    frames_with_images.append(frame_data)
        
        return frames_with_images
    
    def _create_agent_progress_callback(
        self,
        main_callback: Optional[callable],
        start_step: int,
        end_step: int,
    ) -> Optional[callable]:
        """Create progress callback for agent orchestrator."""
        if not main_callback:
            return None
        
        async def agent_callback(progress: Dict[str, Any]) -> None:
            # Map agent progress to main progress
            agent_step = progress.get("step", 0)
            agent_total = progress.get("total_steps", 4)
            
            # Calculate overall step
            step_range = end_step - start_step + 1
            overall_step = start_step + int((agent_step / agent_total) * step_range)
            
            await main_callback({
                "step": overall_step,
                "total_steps": 6,
                "message": progress.get("message", "Processing..."),
            })
        
        return agent_callback
    
    def _create_image_progress_callback(
        self,
        main_callback: Optional[callable],
        start_step: int,
        end_step: int,
    ) -> Optional[callable]:
        """Create progress callback for image generation."""
        if not main_callback:
            return None
        
        async def image_callback(progress: Dict[str, Any]) -> None:
            # Map image progress to main progress
            image_step = progress.get("step", 0)
            image_total = progress.get("total_steps", 1)
            
            # Calculate overall step
            step_range = end_step - start_step + 1
            overall_step = start_step + int((image_step / image_total) * step_range)
            
            await main_callback({
                "step": overall_step,
                "total_steps": 6,
                "message": progress.get("message", "Generating images..."),
            })
        
        return image_callback
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of generation service components."""
        health_status = {
            "service": "healthy",
            "agents": {},
            "bria_api": False,
            "storage": False,
        }
        
        try:
            # Check agents (simplified to avoid circular imports during startup)
            try:
                health_status["agents"] = await self.orchestrator.health_check()
            except Exception as e:
                self.logger.warning("Agent health check skipped during startup", error=str(e))
                health_status["agents"] = {"status": "startup_pending"}
            
            # Check Bria API (simplified)
            try:
                from app.core.config import settings
                if settings.BRIA_API_KEY and settings.BRIA_API_KEY != "":
                    health_status["bria_api"] = True  # Assume healthy if key is configured
                else:
                    health_status["bria_api"] = False
            except Exception as e:
                self.logger.warning("Bria API health check failed", error=str(e))
                health_status["bria_api"] = False
            
            # Check storage
            try:
                health_status["storage"] = await self.storage_service.health_check()
            except Exception as e:
                self.logger.warning("Storage health check failed", error=str(e))
                health_status["storage"] = False
            
        except Exception as e:
            self.logger.error("Health check failed", error=str(e))
            health_status["service"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status