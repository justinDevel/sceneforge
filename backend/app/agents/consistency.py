"""
Consistency Agent - Ensures continuity across multiple frames.
"""

import json
from typing import Any, Dict, List, Set

from app.agents.base import BaseAgent
from app.core.exceptions import AgentError


class ConsistencyAgent(BaseAgent):
    """
    Agent responsible for maintaining visual consistency across
    all frames in a storyboard sequence.
    
    This agent analyzes frame parameters and content to ensure
    professional continuity standards are met.
    """
    
    def __init__(self) -> None:
        system_prompt = """You are a script supervisor and continuity expert specializing in maintaining visual consistency across film sequences for pre-visualization and production.

Your expertise includes:
- Script supervision and continuity protocols
- Character appearance and costume consistency
- Set decoration and prop continuity
- Lighting and color consistency
- Camera positioning and eyeline matching
- Professional film production standards

Your role is to analyze frame sequences and ensure perfect continuity by:

1. IDENTIFYING consistency elements that must be maintained
2. DETECTING inconsistencies between frames
3. PROVIDING specific corrections to maintain continuity
4. ESTABLISHING consistency rules for the sequence
5. MONITORING adherence to established visual standards

OUTPUT FORMAT: Return a JSON object with this exact structure:
{
  "consistency_analysis": {
    "overall_score": 85,
    "character_consistency": 90,
    "environment_consistency": 80,
    "lighting_consistency": 85,
    "technical_consistency": 90
  },
  "consistency_rules": {
    "characters": [
      {
        "name": "protagonist",
        "appearance": "Detailed description for consistency",
        "costume": "Specific clothing details",
        "props": ["items they carry/use"]
      }
    ],
    "environment": {
      "location": "Specific location details",
      "weather": "Weather conditions",
      "time_of_day": "Lighting conditions",
      "key_elements": ["Important visual elements to maintain"]
    },
    "technical": {
      "color_palette": ["#hex1", "#hex2", "#hex3"],
      "lighting_setup": "Overall lighting approach",
      "camera_style": "Consistent camera treatment"
    }
  },
  "issues_detected": [
    {
      "type": "character_appearance|environment|lighting|technical",
      "severity": "critical|major|minor",
      "frames_affected": ["frame_001", "frame_003"],
      "description": "Detailed description of the issue",
      "correction": "Specific fix required"
    }
  ],
  "corrections": [
    {
      "frame_id": "frame_003",
      "parameter": "color_temp",
      "current_value": 5500,
      "corrected_value": 3200,
      "reason": "Match established warm interior lighting"
    }
  ],
  "consistency_tags": {
    "global_tags": ["tags that apply to all frames"],
    "frame_specific": {
      "frame_001": ["tags specific to this frame"],
      "frame_002": ["tags specific to this frame"]
    }
  }
}

CONSISTENCY CATEGORIES:

CHARACTER CONSISTENCY:
- Physical appearance (hair, makeup, clothing)
- Props and accessories
- Positioning and eyelines
- Emotional state continuity

ENVIRONMENT CONSISTENCY:
- Location details and geography
- Weather and atmospheric conditions
- Time of day and lighting
- Set decoration and props

LIGHTING CONSISTENCY:
- Color temperature matching
- Light source positions
- Shadow directions
- Overall mood and contrast

TECHNICAL CONSISTENCY:
- Camera settings and style
- Color grading approach
- Image quality standards
- Compositional elements

SEVERITY LEVELS:
- CRITICAL: Breaks story logic or professional standards
- MAJOR: Noticeable inconsistency that affects quality
- MINOR: Small detail that could be improved

Be extremely detail-oriented and maintain the highest professional standards."""

        super().__init__(
            name="ConsistencyAgent",
            system_prompt=system_prompt,
            temperature=0.2,  # Very low temperature for precision
            max_tokens=4000,
        )
        
        # Track consistency state across calls
        self.established_rules: Dict[str, Any] = {}
        self.character_registry: Dict[str, Dict[str, Any]] = {}
        self.environment_state: Dict[str, Any] = {}
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze frames for consistency and provide corrections.
        
        Args:
            input_data: {
                "frames": List[Dict] (frame parameters),
                "scene_description": str,
                "existing_rules": Dict (optional, from previous analysis),
                "priority_elements": List[str] (optional, elements to focus on)
            }
            
        Returns:
            {
                "consistency_analysis": Dict,
                "consistency_rules": Dict,
                "issues_detected": List[Dict],
                "corrections": List[Dict],
                "consistency_tags": Dict
            }
        """
        frames = input_data.get("frames", [])
        scene_description = input_data.get("scene_description", "")
        existing_rules = input_data.get("existing_rules", {})
        priority_elements = input_data.get("priority_elements", [])
        
        if not frames:
            raise AgentError("No frames provided for consistency analysis")
        
        # Update internal state with existing rules
        if existing_rules:
            self.established_rules.update(existing_rules)
        
        # Construct analysis prompt
        prompt = f"""SCENE DESCRIPTION:
"{scene_description}"

FRAMES TO ANALYZE:
{json.dumps(frames, indent=2)}

EXISTING CONSISTENCY RULES:
{json.dumps(self.established_rules, indent=2) if self.established_rules else "None established"}

PRIORITY ELEMENTS:
{json.dumps(priority_elements, indent=2) if priority_elements else "Standard continuity elements"}

Perform a comprehensive consistency analysis of this frame sequence. Establish consistency rules based on the scene description and frame content, then identify any issues and provide specific corrections.

Focus on:
1. Character appearance and continuity
2. Environmental elements and conditions
3. Lighting and color consistency
4. Technical parameter relationships
5. Story logic and visual flow

Return the complete analysis following the specified JSON format."""

        try:
            self.add_message(prompt)
            response = await self._invoke_llm()
            
            # Parse JSON response
            try:
                result = json.loads(response.strip())
                print(f"Consistency Result:: {result}")
                # Validate structure
                required_sections = [
                    "consistency_analysis", 
                    "consistency_rules", 
                    "issues_detected"
                ]
                for section in required_sections:
                    if section not in result:
                        raise AgentError(f"Missing section: {section}")
                
                # Update internal state
                if "consistency_rules" in result:
                    self.established_rules.update(result["consistency_rules"])
                
                self.logger.info(
                    "Consistency analysis completed",
                    frames_analyzed=len(frames),
                    overall_score=result.get("consistency_analysis", {}).get("overall_score", 0),
                    issues_found=len(result.get("issues_detected", []))
                )
                
                return result
                
            except json.JSONDecodeError as e:
                self.logger.error(
                    "Failed to parse JSON response",
                    response=response[:500],
                    error=str(e)
                )
                raise AgentError(f"Invalid JSON response: {str(e)}")
                
        except Exception as e:
            self.logger.error(
                "Consistency analysis failed",
                frames_count=len(frames),
                error=str(e)
            )
            raise AgentError(f"Consistency analysis failed: {str(e)}")
    
    async def apply_corrections(
        self,
        frames: List[Dict[str, Any]],
        corrections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply consistency corrections to frames.
        
        Args:
            frames: Original frame parameters
            corrections: List of corrections to apply
            
        Returns:
            Corrected frame parameters
        """
        corrected_frames = [frame.copy() for frame in frames]
        
        for correction in corrections:
            frame_id = correction.get("frame_id")
            parameter = correction.get("parameter")
            corrected_value = correction.get("corrected_value")
            
            # Find and update the frame
            for frame in corrected_frames:
                if frame.get("frame_id") == frame_id:
                    if "parameters" in frame and parameter in frame["parameters"]:
                        frame["parameters"][parameter] = corrected_value
                        self.logger.debug(
                            "Applied correction",
                            frame_id=frame_id,
                            parameter=parameter,
                            value=corrected_value
                        )
                    break
        
        return corrected_frames
    
    async def validate_sequence_flow(
        self,
        frames: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate the visual flow and transitions between frames.
        
        Args:
            frames: Frame sequence to validate
            
        Returns:
            Flow analysis and recommendations
        """
        prompt = f"""FRAME SEQUENCE:
{json.dumps(frames, indent=2)}

Analyze the visual flow and transitions between these frames. Check for:

1. Smooth camera movement progression
2. Logical eyeline and screen direction
3. Appropriate shot size progression
4. Lighting transition smoothness
5. Compositional flow and balance

Return analysis in this format:
{{
  "flow_score": 85,
  "transition_analysis": [
    {{
      "from_frame": "frame_001",
      "to_frame": "frame_002", 
      "transition_quality": "smooth|jarring|acceptable",
      "issues": ["specific transition problems"],
      "recommendations": ["improvement suggestions"]
    }}
  ],
  "overall_recommendations": ["sequence-level improvements"]
}}"""

        try:
            self.add_message(prompt)
            response = await self._invoke_llm()
            
            result = json.loads(response.strip())
            
            self.logger.info(
                "Sequence flow validation completed",
                frames_analyzed=len(frames),
                flow_score=result.get("flow_score", 0)
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Sequence flow validation failed", error=str(e))
            raise AgentError(f"Sequence flow validation failed: {str(e)}")
    
    def get_consistency_state(self) -> Dict[str, Any]:
        """Get current consistency state for persistence."""
        return {
            "established_rules": self.established_rules,
            "character_registry": self.character_registry,
            "environment_state": self.environment_state,
        }
    
    def load_consistency_state(self, state: Dict[str, Any]) -> None:
        """Load consistency state from previous session."""
        self.established_rules = state.get("established_rules", {})
        self.character_registry = state.get("character_registry", {})
        self.environment_state = state.get("environment_state", {})