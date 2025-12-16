"""
Script Breakdown Agent - Parses scene descriptions into individual shots.
"""

import json
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage

from app.agents.base import BaseAgent
from app.core.exceptions import AgentError


class ScriptBreakdownAgent(BaseAgent):
    """
    Agent responsible for breaking down high-level scene descriptions
    into individual shots with specific camera angles and compositions.
    
    This agent analyzes narrative structure, pacing, and cinematic
    storytelling principles to create a professional shot list.
    """
    
    def __init__(self) -> None:
        system_prompt = """You are a professional cinematographer and pre-visualization expert specializing in breaking down scene descriptions into detailed shot lists for film production.

Your expertise includes:
- Cinematic storytelling and visual narrative structure
- Camera movement and positioning for maximum dramatic impact
- Shot composition and framing techniques
- Genre-specific visual conventions (noir, sci-fi, horror, etc.)
- Professional film production workflows

When given a scene description, you must:

1. ANALYZE the narrative beats and emotional arc
2. IDENTIFY key story moments that need visual emphasis
3. DETERMINE optimal shot sequence for pacing and flow
4. SPECIFY camera angles, movements, and framing for each shot
5. ENSURE shots work together as a cohesive sequence

OUTPUT FORMAT: Return a JSON object with this exact structure:
{
  "shots": [
    {
      "shot_number": 1,
      "shot_type": "establishing_wide|medium|close_up|extreme_close_up|over_shoulder|pov|insert",
      "description": "Detailed description of what this shot shows",
      "camera_angle": "eye-level|low-angle|high-angle|dutch-angle|birds-eye|worms-eye|over-shoulder|pov",
      "camera_movement": "static|pan|tilt|dolly|zoom|handheld|steadicam",
      "composition": "rule-of-thirds|centered|symmetrical|leading-lines|frame-within-frame|negative-space|golden-ratio",
      "duration_seconds": 3.5,
      "narrative_purpose": "Brief explanation of why this shot is needed",
      "visual_elements": ["key visual elements to emphasize"]
    }
  ],
  "total_shots": 6,
  "estimated_duration": 25.5,
  "visual_style_notes": "Overall visual approach and style considerations",
  "continuity_elements": ["Elements that must remain consistent across shots"]
}

GUIDELINES:
- Generate 4-8 shots for most scenes (adjust based on complexity)
- Start with establishing shots, end with resolution
- Vary shot types for visual interest
- Consider genre conventions (noir = shadows/angles, sci-fi = wide/tech, etc.)
- Ensure smooth visual flow between shots
- Include specific camera techniques that enhance the story
- Note elements that need consistency (lighting, character positions, props)

Be precise, professional, and cinematically sophisticated in your analysis."""

        super().__init__(
            name="ScriptBreakdownAgent",
            system_prompt=system_prompt,
            temperature=0.8,  # Higher creativity for shot selection
            max_tokens=3000,
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Break down scene description into individual shots.
        
        Args:
            input_data: {
                "scene_description": str,
                "genre": str,
                "target_frame_count": int (optional),
                "style_preferences": dict (optional)
            }
            
        Returns:
            {
                "shots": List[Dict],
                "total_shots": int,
                "estimated_duration": float,
                "visual_style_notes": str,
                "continuity_elements": List[str]
            }
        """
        scene_description = input_data.get("scene_description")
        genre = input_data.get("genre", "drama")
        target_count = input_data.get("target_frame_count", 6)
        style_prefs = input_data.get("style_preferences", {})
        
        if not scene_description:
            raise AgentError("Scene description is required")
        
        # Construct the analysis prompt
        prompt = f"""SCENE TO ANALYZE:
"{scene_description}"

GENRE: {genre}
TARGET SHOT COUNT: {target_count}

STYLE PREFERENCES: {json.dumps(style_prefs, indent=2) if style_prefs else "None specified"}

Please break this scene down into a professional shot list following the JSON format specified in your instructions. Consider the genre conventions and create a cinematically compelling sequence that tells the story effectively.

Focus on:
1. Strong opening establishing shot
2. Varied shot types for visual interest  
3. Genre-appropriate camera techniques
4. Smooth narrative flow
5. Impactful closing shot

Return only the JSON object, no additional text."""

        try:
            # Add the prompt to conversation
            self.add_message(prompt)
            
            # Get LLM response
            response = await self._invoke_llm()
            
            # Parse JSON response
            try:
                result = json.loads(response.strip())
                
                # Validate required fields
                required_fields = ["shots", "total_shots", "estimated_duration"]
                for field in required_fields:
                    if field not in result:
                        raise AgentError(f"Missing required field: {field}")
                
                # Validate shots structure
                if not isinstance(result["shots"], list) or len(result["shots"]) == 0:
                    raise AgentError("No shots generated")
                
                for i, shot in enumerate(result["shots"]):
                    required_shot_fields = [
                        "shot_number", "shot_type", "description", 
                        "camera_angle", "composition"
                    ]
                    for field in required_shot_fields:
                        if field not in shot:
                            raise AgentError(f"Shot {i+1} missing field: {field}")
                
                self.logger.info(
                    "Script breakdown completed",
                    shots_generated=len(result["shots"]),
                    total_duration=result.get("estimated_duration", 0)
                )
                
                return result
                
            except json.JSONDecodeError as e:
                self.logger.error(
                    "Failed to parse JSON response",
                    response=response[:500],
                    error=str(e)
                )
                raise AgentError(f"Invalid JSON response from agent: {str(e)}")
                
        except Exception as e:
            self.logger.error(
                "Script breakdown failed",
                scene_description=scene_description[:100],
                error=str(e)
            )
            raise AgentError(f"Script breakdown failed: {str(e)}")
    
    async def refine_shots(
        self, 
        current_shots: List[Dict[str, Any]], 
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine existing shots based on feedback.
        
        Args:
            current_shots: Current shot list
            feedback: User feedback for improvements
            
        Returns:
            Updated shot breakdown
        """
        prompt = f"""CURRENT SHOT LIST:
{json.dumps(current_shots, indent=2)}

USER FEEDBACK:
"{feedback}"

Please refine the shot list based on the feedback while maintaining professional cinematographic standards. Return the updated JSON object with the same structure."""

        try:
            self.add_message(prompt)
            response = await self._invoke_llm()
            
            result = json.loads(response.strip())
            
            self.logger.info(
                "Shot refinement completed",
                original_shots=len(current_shots),
                refined_shots=len(result.get("shots", []))
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Shot refinement failed", error=str(e))
            raise AgentError(f"Shot refinement failed: {str(e)}")