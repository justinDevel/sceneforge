"""
JSON Structuring Agent - Converts natural language to precise JSON parameters.
"""

import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.core.exceptions import AgentError


class JSONStructuringAgent(BaseAgent):
    """
    Agent responsible for converting natural language shot descriptions
    into precise JSON parameters for Bria FIBO image generation.
    
    This agent specializes in translating cinematic concepts into
    technical parameters that produce professional-quality results.
    """
    
    def __init__(self) -> None:
        system_prompt = """You are a technical director and digital cinematography expert specializing in converting creative vision into precise technical parameters for AI image generation using Bria FIBO.

Your expertise includes:
- Professional camera specifications and settings
- Lighting design and color theory
- Digital image composition and framing
- HDR and color space management
- Technical parameter optimization for AI generation

When given shot descriptions, you must convert them into precise JSON parameters that will produce professional, cinematic results.

OUTPUT FORMAT: Return a JSON object with this exact structure:
{
  "frames": [
    {
      "frame_id": "frame_001",
      "prompt": "Detailed, technical prompt optimized for FIBO",
      "negative_prompt": "Elements to avoid",
      "parameters": {
        "fov": 35,
        "lighting": 75,
        "hdr_bloom": 40,
        "color_temp": 3200,
        "contrast": 60,
        "camera_angle": "low-angle",
        "composition": "rule-of-thirds"
      },
      "technical_notes": "Explanation of parameter choices",
      "consistency_tags": ["character_appearance", "environment_lighting", "weather_conditions"]
    }
  ],
  "global_consistency": {
    "character_descriptions": ["Detailed character appearance for consistency"],
    "environment_elements": ["Key environment features to maintain"],
    "lighting_setup": "Overall lighting approach",
    "color_palette": "Dominant colors and mood",
    "visual_style": "Overall aesthetic approach"
  }
}

PARAMETER GUIDELINES:

FOV (Field of View):
- 14-24mm: Ultra-wide, dramatic perspective, architectural
- 24-35mm: Wide angle, environmental context, establishing shots
- 35-50mm: Standard, natural perspective, medium shots
- 50-85mm: Portrait, close-ups, character focus
- 85-135mm: Telephoto, compression, isolation, dramatic close-ups

LIGHTING (0-100):
- 0-20: Very dark, noir, horror, dramatic shadows
- 20-40: Low key, moody, intimate scenes
- 40-60: Balanced, natural lighting
- 60-80: Bright, commercial, clean lighting
- 80-100: High key, overexposed, ethereal, sci-fi

HDR BLOOM (0-100):
- 0-20: Minimal bloom, realistic
- 20-40: Subtle enhancement, cinematic
- 40-60: Noticeable bloom, dramatic
- 60-80: Strong bloom, stylized
- 80-100: Extreme bloom, fantasy/sci-fi

COLOR TEMPERATURE (Kelvin):
- 2000-3000K: Warm, candlelight, sunset, cozy
- 3000-4000K: Warm white, tungsten, indoor
- 4000-5000K: Neutral white, fluorescent
- 5000-6500K: Daylight, natural, outdoor
- 6500-10000K: Cool, blue, moonlight, sci-fi

CONTRAST (0-100):
- 0-30: Low contrast, soft, dreamy, fog
- 30-50: Moderate contrast, natural
- 50-70: High contrast, dramatic, defined
- 70-100: Extreme contrast, stark, graphic

PROMPT OPTIMIZATION:
- Use professional cinematography terminology
- Include specific technical details (lens, lighting setup)
- Mention camera brand/model for style (RED, ARRI, etc.)
- Specify film stock emulation if relevant
- Include composition and framing details
- Add atmospheric and mood descriptors
- Use industry-standard color grading terms

CONSISTENCY REQUIREMENTS:
- Character appearance must be identical across shots
- Lighting conditions should match unless story requires change
- Environmental elements must remain consistent
- Props and costumes should maintain continuity
- Weather and atmospheric conditions should be stable

Be technically precise and cinematically sophisticated."""

        super().__init__(
            name="JSONStructuringAgent",
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for precision
            max_tokens=4000,
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert shot descriptions to JSON parameters.
        
        Args:
            input_data: {
                "shots": List[Dict] (from ScriptBreakdownAgent),
                "genre": str,
                "base_params": Dict (optional),
                "consistency_requirements": Dict (optional)
            }
            
        Returns:
            {
                "frames": List[Dict],
                "global_consistency": Dict
            }
        """
        shots = input_data.get("shots", [])
        genre = input_data.get("genre", "drama")
        base_params = input_data.get("base_params", {})
        consistency_reqs = input_data.get("consistency_requirements", {})
        
        if not shots:
            raise AgentError("No shots provided for JSON structuring")
        
        # Construct the conversion prompt
        prompt = f"""SHOTS TO CONVERT:
{json.dumps(shots, indent=2)}

GENRE: {genre}
BASE PARAMETERS: {json.dumps(base_params, indent=2) if base_params else "None"}
CONSISTENCY REQUIREMENTS: {json.dumps(consistency_reqs, indent=2) if consistency_reqs else "Standard film continuity"}

Convert these shots into precise technical parameters for Bria FIBO image generation. Each shot should have:

1. OPTIMIZED PROMPT: Professional cinematography description with technical details
2. NEGATIVE PROMPT: Elements to avoid for quality
3. PRECISE PARAMETERS: Technical settings based on shot requirements
4. CONSISTENCY TAGS: Elements that must remain consistent

Consider:
- Genre-specific visual conventions
- Professional camera and lighting techniques
- Technical parameter relationships (FOV affects perspective, lighting affects mood)
- Continuity requirements across the sequence
- Optimal settings for AI generation quality

Return only the JSON object following the specified format."""

        try:
            self.add_message(prompt)
            response = await self._invoke_llm()
            
            # Parse JSON response
            try:
                result = json.loads(response.strip())
                
                # Validate structure
                if "frames" not in result:
                    raise AgentError("Missing 'frames' in response")
                
                if not isinstance(result["frames"], list):
                    raise AgentError("'frames' must be a list")
                
                # Validate each frame
                for i, frame in enumerate(result["frames"]):
                    required_fields = ["frame_id", "prompt", "parameters"]
                    for field in required_fields:
                        if field not in frame:
                            raise AgentError(f"Frame {i+1} missing field: {field}")
                    
                    # Validate parameters
                    params = frame["parameters"]
                    required_params = ["fov", "lighting", "camera_angle", "composition"]
                    for param in required_params:
                        if param not in params:
                            raise AgentError(f"Frame {i+1} missing parameter: {param}")
                
                self.logger.info(
                    "JSON structuring completed",
                    frames_generated=len(result["frames"]),
                    has_global_consistency="global_consistency" in result
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
                "JSON structuring failed",
                shots_count=len(shots),
                error=str(e)
            )
            raise AgentError(f"JSON structuring failed: {str(e)}")
    
    async def optimize_parameters(
        self,
        frame_data: Dict[str, Any],
        optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize parameters for specific goals.
        
        Args:
            frame_data: Current frame parameters
            optimization_goals: List of goals (e.g., ["dramatic_lighting", "wide_perspective"])
            
        Returns:
            Optimized frame parameters
        """
        prompt = f"""CURRENT FRAME:
{json.dumps(frame_data, indent=2)}

OPTIMIZATION GOALS:
{json.dumps(optimization_goals, indent=2)}

Optimize the technical parameters to better achieve these goals while maintaining professional quality. Consider parameter interactions and technical constraints.

Return the updated frame object with the same structure."""

        try:
            self.add_message(prompt)
            response = await self._invoke_llm()
            
            result = json.loads(response.strip())
            
            self.logger.info(
                "Parameter optimization completed",
                goals=optimization_goals,
                frame_id=frame_data.get("frame_id", "unknown")
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Parameter optimization failed", error=str(e))
            raise AgentError(f"Parameter optimization failed: {str(e)}")
    
    async def validate_consistency(
        self,
        frames: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate consistency across frames and suggest improvements.
        
        Args:
            frames: List of frame parameters
            
        Returns:
            Consistency analysis and recommendations
        """
        prompt = f"""FRAME SEQUENCE:
{json.dumps(frames, indent=2)}

Analyze this frame sequence for consistency issues and provide recommendations for improvement. Check:

1. Character appearance consistency
2. Lighting continuity
3. Environmental elements
4. Color palette coherence
5. Technical parameter relationships

Return analysis in this format:
{{
  "consistency_score": 85,
  "issues_found": [
    {{
      "type": "lighting_mismatch",
      "frames": ["frame_001", "frame_003"],
      "description": "Lighting temperature inconsistent",
      "severity": "medium",
      "recommendation": "Adjust color_temp to match"
    }}
  ],
  "recommendations": [
    "Specific improvement suggestions"
  ]
}}"""

        try:
            self.add_message(prompt)
            response = await self._invoke_llm()
            
            result = json.loads(response.strip())
            
            self.logger.info(
                "Consistency validation completed",
                frames_analyzed=len(frames),
                consistency_score=result.get("consistency_score", 0)
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Consistency validation failed", error=str(e))
            raise AgentError(f"Consistency validation failed: {str(e)}")