"""
Refinement Agent - Handles user feedback and iterative improvements.
"""

import json
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.core.exceptions import AgentError


class RefinementAgent(BaseAgent):
    """
    Agent responsible for processing user feedback and making
    targeted improvements to generated frames while maintaining
    overall sequence consistency.
    
    This agent specializes in interpreting creative direction
    and translating it into precise parameter adjustments.
    """
    
    def __init__(self) -> None:
        system_prompt = """You are a creative director and technical supervisor specializing in iterative refinement of pre-visualization content based on director feedback.

Your expertise includes:
- Interpreting creative direction and artistic feedback
- Translating subjective feedback into technical parameters
- Maintaining sequence consistency during refinements
- Balancing creative vision with technical constraints
- Professional film production iteration workflows

When processing refinement requests, you must:

1. ANALYZE the feedback to understand the creative intent
2. IDENTIFY which technical parameters need adjustment
3. CALCULATE precise parameter changes to achieve the desired result
4. ENSURE changes don't break sequence consistency
5. PROVIDE clear explanations for all modifications

OUTPUT FORMAT: Return a JSON object with this exact structure:
{
  "refinement_analysis": {
    "feedback_interpretation": "Clear understanding of what the user wants",
    "affected_elements": ["list of elements that need changes"],
    "change_scope": "single_frame|multiple_frames|sequence_wide",
    "consistency_impact": "none|minor|major",
    "technical_feasibility": "high|medium|low"
  },
  "parameter_changes": [
    {
      "frame_id": "frame_003",
      "parameter": "lighting",
      "current_value": 60,
      "new_value": 85,
      "change_reason": "Increase brightness for more dramatic effect",
      "confidence": 0.9
    }
  ],
  "prompt_modifications": [
    {
      "frame_id": "frame_001",
      "current_prompt": "Current prompt text",
      "modified_prompt": "Updated prompt with refinements",
      "changes_made": ["specific changes to the prompt"]
    }
  ],
  "consistency_adjustments": [
    {
      "affected_frames": ["frame_002", "frame_004"],
      "adjustment_type": "lighting_compensation",
      "description": "Adjust related frames to maintain consistency",
      "parameters": {"color_temp": 3200}
    }
  ],
  "alternative_approaches": [
    {
      "approach": "Alternative method description",
      "pros": ["advantages of this approach"],
      "cons": ["potential drawbacks"],
      "parameters": {"suggested parameter changes"}
    }
  ]
}

FEEDBACK INTERPRETATION GUIDELINES:

LIGHTING FEEDBACK:
- "too dark/bright" → adjust lighting parameter
- "more dramatic" → increase contrast, adjust shadows
- "warmer/cooler" → modify color temperature
- "more atmospheric" → increase hdr_bloom, adjust lighting
- "harsh/soft" → modify contrast and lighting intensity

COMPOSITION FEEDBACK:
- "closer/wider" → adjust FOV
- "more dynamic" → change camera angle to low/high
- "better framing" → modify composition rule
- "more intimate" → decrease FOV, change to close-up
- "more epic" → increase FOV, use wide angle

MOOD FEEDBACK:
- "more intense" → increase contrast, dramatic lighting
- "softer" → decrease contrast, warmer color temp
- "more cinematic" → adjust multiple parameters for film look
- "more realistic" → reduce HDR bloom, natural lighting
- "stylized" → increase artistic parameters

TECHNICAL FEEDBACK:
- "sharper" → adjust technical quality parameters
- "more depth" → modify FOV and composition
- "better colors" → adjust color temperature and contrast
- "more professional" → optimize all parameters for quality

CONSISTENCY CONSIDERATIONS:
- Single frame changes should not break sequence flow
- Lighting changes may require adjustments to adjacent frames
- Character appearance must remain consistent
- Environmental elements should maintain continuity
- Camera style should remain coherent throughout sequence

Be precise in parameter calculations and always explain your reasoning."""

        super().__init__(
            name="RefinementAgent",
            system_prompt=system_prompt,
            temperature=0.4,  # Balanced creativity and precision
            max_tokens=3500,
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process refinement feedback and generate parameter adjustments.
        
        Args:
            input_data: {
                "feedback": str (user feedback),
                "target_frame_id": str (optional, specific frame to refine),
                "current_frames": List[Dict] (current frame parameters),
                "consistency_rules": Dict (optional, established consistency rules),
                "refinement_history": List[Dict] (optional, previous refinements)
            }
            
        Returns:
            {
                "refinement_analysis": Dict,
                "parameter_changes": List[Dict],
                "prompt_modifications": List[Dict],
                "consistency_adjustments": List[Dict],
                "alternative_approaches": List[Dict]
            }
        """
        feedback = input_data.get("feedback")
        target_frame_id = input_data.get("target_frame_id")
        current_frames = input_data.get("current_frames", [])
        consistency_rules = input_data.get("consistency_rules", {})
        refinement_history = input_data.get("refinement_history", [])
        
        if not feedback:
            raise AgentError("Feedback is required for refinement")
        
        if not current_frames:
            raise AgentError("Current frames are required for refinement")
        
        # Construct refinement prompt
        prompt = f"""USER FEEDBACK:
"{feedback}"

TARGET FRAME: {target_frame_id if target_frame_id else "Not specified - analyze all frames"}

CURRENT FRAMES:
{json.dumps(current_frames, indent=2)}

CONSISTENCY RULES:
{json.dumps(consistency_rules, indent=2) if consistency_rules else "No specific rules established"}

REFINEMENT HISTORY:
{json.dumps(refinement_history, indent=2) if refinement_history else "No previous refinements"}

Analyze this feedback and provide precise refinement instructions. Consider:

1. What specific visual changes are being requested?
2. Which technical parameters need adjustment?
3. How will changes affect sequence consistency?
4. Are there alternative approaches to achieve the goal?
5. What are the technical constraints and feasibility?

Provide detailed parameter changes and clear reasoning for each modification."""

        try:
            self.add_message(prompt)
            response = await self._invoke_llm()
            
            # Parse JSON response
            try:
                result = json.loads(response.strip())
                
                # Validate structure
                required_sections = ["refinement_analysis", "parameter_changes"]
                for section in required_sections:
                    if section not in result:
                        raise AgentError(f"Missing section: {section}")
                
                # Validate parameter changes
                for change in result.get("parameter_changes", []):
                    required_fields = ["frame_id", "parameter", "new_value"]
                    for field in required_fields:
                        if field not in change:
                            raise AgentError(f"Parameter change missing field: {field}")
                
                self.logger.info(
                    "Refinement analysis completed",
                    feedback_length=len(feedback),
                    parameter_changes=len(result.get("parameter_changes", [])),
                    consistency_impact=result.get("refinement_analysis", {}).get("consistency_impact", "unknown")
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
                "Refinement analysis failed",
                feedback=feedback[:100],
                error=str(e)
            )
            raise AgentError(f"Refinement analysis failed: {str(e)}")
    
    async def apply_refinements(
        self,
        frames: List[Dict[str, Any]],
        refinement_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply refinement changes to frames.
        
        Args:
            frames: Original frame parameters
            refinement_result: Result from process() method
            
        Returns:
            Updated frame parameters
        """
        refined_frames = [frame.copy() for frame in frames]
        
        # Apply parameter changes
        for change in refinement_result.get("parameter_changes", []):
            frame_id = change.get("frame_id")
            parameter = change.get("parameter")
            new_value = change.get("new_value")
            
            for frame in refined_frames:
                if frame.get("frame_id") == frame_id:
                    if "parameters" in frame:
                        frame["parameters"][parameter] = new_value
                        self.logger.debug(
                            "Applied parameter change",
                            frame_id=frame_id,
                            parameter=parameter,
                            new_value=new_value
                        )
                    break
        
        # Apply prompt modifications
        for mod in refinement_result.get("prompt_modifications", []):
            frame_id = mod.get("frame_id")
            modified_prompt = mod.get("modified_prompt")
            
            for frame in refined_frames:
                if frame.get("frame_id") == frame_id and modified_prompt:
                    frame["prompt"] = modified_prompt
                    self.logger.debug(
                        "Applied prompt modification",
                        frame_id=frame_id
                    )
                    break
        
        # Apply consistency adjustments
        for adjustment in refinement_result.get("consistency_adjustments", []):
            affected_frames = adjustment.get("affected_frames", [])
            parameters = adjustment.get("parameters", {})
            
            for frame in refined_frames:
                if frame.get("frame_id") in affected_frames:
                    if "parameters" in frame:
                        frame["parameters"].update(parameters)
                        self.logger.debug(
                            "Applied consistency adjustment",
                            frame_id=frame.get("frame_id"),
                            parameters=parameters
                        )
        
        return refined_frames
    
    async def suggest_improvements(
        self,
        frames: List[Dict[str, Any]],
        quality_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Suggest proactive improvements based on analysis.
        
        Args:
            frames: Current frame parameters
            quality_metrics: Optional quality analysis results
            
        Returns:
            Improvement suggestions
        """
        prompt = f"""CURRENT FRAMES:
{json.dumps(frames, indent=2)}

QUALITY METRICS:
{json.dumps(quality_metrics, indent=2) if quality_metrics else "No metrics provided"}

Analyze these frames and suggest proactive improvements to enhance:
1. Visual quality and professionalism
2. Cinematic storytelling effectiveness
3. Technical parameter optimization
4. Sequence flow and pacing
5. Overall artistic impact

Return suggestions in this format:
{{
  "improvement_categories": [
    {{
      "category": "lighting_enhancement",
      "priority": "high|medium|low",
      "description": "What improvements are suggested",
      "affected_frames": ["frame_001"],
      "parameter_changes": {{"lighting": 75}},
      "expected_impact": "Specific improvement expected"
    }}
  ],
  "sequence_optimizations": [
    "Overall sequence improvements"
  ],
  "creative_alternatives": [
    "Alternative creative approaches to consider"
  ]
}}"""

        try:
            self.add_message(prompt)
            response = await self._invoke_llm()
            
            result = json.loads(response.strip())
            
            self.logger.info(
                "Improvement suggestions generated",
                frames_analyzed=len(frames),
                suggestions_count=len(result.get("improvement_categories", []))
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Improvement suggestion failed", error=str(e))
            raise AgentError(f"Improvement suggestion failed: {str(e)}")