"""
Agent Orchestrator - Coordinates the agentic workflow for scene generation.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.consistency import ConsistencyAgent
from app.agents.json_structuring import JSONStructuringAgent
from app.agents.refinement import RefinementAgent
from app.agents.script_breakdown import ScriptBreakdownAgent
from app.core.exceptions import AgentError
from app.core.logging import LoggerMixin
from app.models.schemas import FrameParams, Genre


class AgentOrchestrator(LoggerMixin):
    """
    Orchestrates the collaboration between specialized AI agents
    to transform scene descriptions into professional storyboards.
    
    Workflow:
    1. ScriptBreakdownAgent: Parse scene into shots
    2. JSONStructuringAgent: Convert shots to technical parameters
    3. ConsistencyAgent: Ensure continuity across frames
    4. RefinementAgent: Apply user feedback (when needed)
    """
    
    def __init__(self) -> None:
        # Initialize agents
        self.script_agent = ScriptBreakdownAgent()
        self.json_agent = JSONStructuringAgent()
        self.consistency_agent = ConsistencyAgent()
        self.refinement_agent = RefinementAgent()
        
        # Track workflow state
        self.workflow_state: Dict[str, Any] = {}
        self.generation_metrics: Dict[str, Any] = {}
    
    async def generate_storyboard(
        self,
        scene_description: str,
        genre: Genre,
        frame_count: int = 6,
        base_params: Optional[FrameParams] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate complete storyboard through agentic workflow.
        
        Args:
            scene_description: High-level scene description
            genre: Film genre for style guidance
            frame_count: Target number of frames
            base_params: Base parameters for generation
            progress_callback: Optional callback for progress updates
            
        Returns:
            Complete storyboard with frames and metadata
        """
        workflow_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.logger.info(
            "Starting storyboard generation",
            workflow_id=workflow_id,
            scene_length=len(scene_description),
            genre=genre.value,
            frame_count=frame_count
        )
        
        try:
            # Initialize workflow state
            self.workflow_state = {
                "workflow_id": workflow_id,
                "scene_description": scene_description,
                "genre": genre,
                "frame_count": frame_count,
                "base_params": base_params.dict() if base_params else {},
                "start_time": start_time,
                "steps_completed": 0,
                "total_steps": 4,
            }
            
            # Step 1: Script Breakdown
            await self._update_progress(
                "Analyzing scene structure and breaking down into shots...",
                1, progress_callback
            )
            
            # Add genre information to agent conversation
            self.script_agent.add_message(f"GENRE: {genre.value.upper()}")
            
            breakdown_result = await self.script_agent.process({
                "scene_description": scene_description,
                "genre": genre.value,
                "target_frame_count": frame_count,
                "style_preferences": {}
            })
            
            self.workflow_state["breakdown_result"] = breakdown_result
            
            # Step 2: JSON Structuring
            await self._update_progress(
                "Converting shots to technical parameters...",
                2, progress_callback
            )
            
            structuring_result = await self.json_agent.process({
                "shots": breakdown_result["shots"],
                "genre": genre.value,
                "base_params": base_params.dict() if base_params else {},
                "consistency_requirements": {}
            })
            
            self.workflow_state["structuring_result"] = structuring_result
            
            # Step 3: Consistency Analysis
            await self._update_progress(
                "Ensuring consistency across all frames...",
                3, progress_callback
            )
            
            consistency_result = await self.consistency_agent.process({
                "frames": structuring_result["frames"],
                "scene_description": scene_description,
                "existing_rules": {},
                "priority_elements": []
            })
            
            # Apply consistency corrections
            corrected_frames = await self.consistency_agent.apply_corrections(
                structuring_result["frames"],
                consistency_result.get("corrections", [])
            )
            
            self.workflow_state["consistency_result"] = consistency_result
            self.workflow_state["final_frames"] = corrected_frames
            
            # Step 4: Final Validation
            await self._update_progress(
                "Finalizing storyboard and preparing output...",
                4, progress_callback
            )
            
            # Validate sequence flow
            flow_analysis = await self.consistency_agent.validate_sequence_flow(
                corrected_frames
            )
            
            # Compile final result
            end_time = datetime.utcnow()
            generation_time = (end_time - start_time).total_seconds()
            
            result = {
                "workflow_id": workflow_id,
                "frames": corrected_frames,
                "metadata": {
                    "scene_description": scene_description,
                    "genre": genre.value,
                    "frame_count": len(corrected_frames),
                    "generation_time": generation_time,
                    "created_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat(),
                },
                "breakdown_summary": {
                    "total_shots": breakdown_result.get("total_shots", 0),
                    "estimated_duration": breakdown_result.get("estimated_duration", 0),
                    "visual_style_notes": breakdown_result.get("visual_style_notes", ""),
                },
                "consistency_analysis": {
                    "overall_score": consistency_result.get("consistency_analysis", {}).get("overall_score", 0),
                    "issues_detected": len(consistency_result.get("issues_detected", [])),
                    "corrections_applied": len(consistency_result.get("corrections", [])),
                },
                "flow_analysis": flow_analysis,
                "global_consistency": structuring_result.get("global_consistency", {}),
                "agent_metrics": self._compile_agent_metrics(),
            }
            
            self.logger.info(
                "Storyboard generation completed",
                workflow_id=workflow_id,
                frames_generated=len(corrected_frames),
                generation_time=generation_time,
                consistency_score=consistency_result.get("consistency_analysis", {}).get("overall_score", 0)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Storyboard generation failed",
                workflow_id=workflow_id,
                error=str(e),
                step=self.workflow_state.get("steps_completed", 0)
            )
            raise AgentError(f"Storyboard generation failed: {str(e)}")
    
    async def refine_storyboard(
        self,
        current_frames: List[Dict[str, Any]],
        feedback: str,
        target_frame_id: Optional[str] = None,
        consistency_rules: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Refine existing storyboard based on user feedback.
        
        Args:
            current_frames: Current frame parameters
            feedback: User feedback for improvements
            target_frame_id: Optional specific frame to refine
            consistency_rules: Established consistency rules
            progress_callback: Optional progress callback
            
        Returns:
            Refined storyboard with updated frames
        """
        refinement_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.logger.info(
            "Starting storyboard refinement",
            refinement_id=refinement_id,
            feedback_length=len(feedback),
            target_frame=target_frame_id,
            frames_count=len(current_frames)
        )
        
        try:
            # Step 1: Analyze feedback
            await self._update_progress(
                "Analyzing feedback and planning refinements...",
                1, progress_callback, total_steps=3
            )
            
            refinement_result = await self.refinement_agent.process({
                "feedback": feedback,
                "target_frame_id": target_frame_id,
                "current_frames": current_frames,
                "consistency_rules": consistency_rules or {},
                "refinement_history": []
            })
            
            # Step 2: Apply refinements
            await self._update_progress(
                "Applying refinements to frames...",
                2, progress_callback, total_steps=3
            )
            
            refined_frames = await self.refinement_agent.apply_refinements(
                current_frames,
                refinement_result
            )
            
            # Step 3: Validate consistency after refinement
            await self._update_progress(
                "Validating consistency after refinements...",
                3, progress_callback, total_steps=3
            )
            
            # Re-check consistency if major changes were made
            consistency_impact = refinement_result.get("refinement_analysis", {}).get("consistency_impact", "none")
            
            if consistency_impact in ["major", "minor"]:
                consistency_check = await self.consistency_agent.process({
                    "frames": refined_frames,
                    "scene_description": "",  # Not needed for validation
                    "existing_rules": consistency_rules or {},
                    "priority_elements": []
                })
                
                # Apply any additional corrections
                if consistency_check.get("corrections"):
                    refined_frames = await self.consistency_agent.apply_corrections(
                        refined_frames,
                        consistency_check["corrections"]
                    )
            
            end_time = datetime.utcnow()
            refinement_time = (end_time - start_time).total_seconds()
            
            result = {
                "refinement_id": refinement_id,
                "frames": refined_frames,
                "refinement_analysis": refinement_result.get("refinement_analysis", {}),
                "changes_applied": {
                    "parameter_changes": len(refinement_result.get("parameter_changes", [])),
                    "prompt_modifications": len(refinement_result.get("prompt_modifications", [])),
                    "consistency_adjustments": len(refinement_result.get("consistency_adjustments", [])),
                },
                "alternative_approaches": refinement_result.get("alternative_approaches", []),
                "metadata": {
                    "feedback": feedback,
                    "target_frame_id": target_frame_id,
                    "refinement_time": refinement_time,
                    "created_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat(),
                },
            }
            
            self.logger.info(
                "Storyboard refinement completed",
                refinement_id=refinement_id,
                changes_applied=result["changes_applied"],
                refinement_time=refinement_time
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Storyboard refinement failed",
                refinement_id=refinement_id,
                error=str(e)
            )
            raise AgentError(f"Storyboard refinement failed: {str(e)}")
    
    async def _update_progress(
        self,
        message: str,
        step: int,
        callback: Optional[callable] = None,
        total_steps: int = 4
    ) -> None:
        """Update progress and call callback if provided."""
        if callback:
            try:
                await callback({
                    "step": step,
                    "total_steps": total_steps,
                    "message": message,
                    "is_complete": step >= total_steps,
                })
            except Exception as e:
                self.logger.warning(
                    "Progress callback failed",
                    error=str(e)
                )
        
        self.workflow_state["steps_completed"] = step
        self.workflow_state["current_message"] = message
    
    def _compile_agent_metrics(self) -> Dict[str, Any]:
        """Compile usage metrics from all agents."""
        return {
            "script_breakdown": self.script_agent.get_usage_stats(),
            "json_structuring": self.json_agent.get_usage_stats(),
            "consistency": self.consistency_agent.get_usage_stats(),
            "refinement": self.refinement_agent.get_usage_stats(),
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all agents."""
        health_status = {}
        
        agents = [
            ("script_breakdown", self.script_agent),
            ("json_structuring", self.json_agent),
            ("consistency", self.consistency_agent),
            ("refinement", self.refinement_agent),
        ]
        
        for name, agent in agents:
            try:
                # Simple test to verify agent is responsive
                from langchain_core.messages import HumanMessage
                test_result = await agent._invoke_llm([
                    HumanMessage(content="Health check - respond with 'OK'")
                ])
                health_status[name] = "OK" in test_result or "mock_response" in test_result
            except Exception as e:
                self.logger.error(f"Agent {name} health check failed", error=str(e))
                health_status[name] = False
        
        return health_status
    
    def get_workflow_state(self) -> Dict[str, Any]:
        """Get current workflow state."""
        return self.workflow_state.copy()
    
    async def cleanup(self) -> None:
        """Cleanup resources and reset state."""
        self.workflow_state.clear()
        self.generation_metrics.clear()
        
        # Reset agent conversation histories
        for agent in [self.script_agent, self.json_agent, self.consistency_agent, self.refinement_agent]:
            agent.reset_conversation()