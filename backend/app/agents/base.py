"""
Base agent class for SceneForge AI agents.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.logging import LoggerMixin


class BaseAgent(LoggerMixin, ABC):
    """
    Base class for all SceneForge AI agents.
    
    Provides common functionality:
    - OpenAI client management
    - Message handling
    - Error handling and logging
    - Token usage tracking
    """
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        model: str = "gemini-1.5-flash-latest",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        
        self.llm = None
        if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "":
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=settings.GEMINI_MODEL,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    google_api_key=settings.GOOGLE_API_KEY,
                )
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini client: {e}")
                self.llm = None
        
        
        self.messages: List[BaseMessage] = [
            SystemMessage(content=system_prompt)
        ]
        
        
        self.total_tokens = 0
        self.total_cost = 0.0
    
    def add_message(self, content: str, role: str = "human") -> None:
        """Add a message to the conversation history."""
        if role == "human":
            self.messages.append(HumanMessage(content=content))
        elif role == "assistant":
            self.messages.append(AIMessage(content=content))
        else:
            self.messages.append(HumanMessage(content=content))
    
    async def _invoke_llm(self, messages: Optional[List[BaseMessage]] = None) -> str:
        """Invoke the LLM with error handling and logging."""
        if messages is None:
            messages = self.messages
        
        try:
            self.logger.info(
                "Invoking LLM",
                agent=self.name,
                model=self.model,
                message_count=len(messages)
            )
            
            
            if not self.llm or not settings.GOOGLE_API_KEY or settings.GOOGLE_API_KEY == "":
                
                self.logger.warning(
                    "Using mock response - Google API key not configured",
                    agent=self.name
                )
                return self._get_mock_response()
            
            
            response = await self.llm.ainvoke(messages)
            print(f"Ai Response:: {response}")
            
            estimated_tokens = len(str(messages)) // 4  
            self.total_tokens += estimated_tokens
            
            self.logger.info(
                "LLM response received",
                agent=self.name,
                response_length=len(response.content),
                estimated_tokens=estimated_tokens
            )
            
            return response.content
            
        except Exception as e:
            self.logger.error(
                "LLM invocation failed",
                agent=self.name,
                error=str(e)
            )
            
            return self._get_mock_response()
    
    def _get_mock_response(self) -> str:
        """Get mock response when Google API is not available."""
        if "ScriptBreakdownAgent" in self.name:
            
            genre = "noir"  
            if self.messages:
                
                for message in self.messages:
                    content = message.content
                    if "GENRE:" in content:
                        genre_line = [line for line in content.split('\n') if 'GENRE:' in line]
                        if genre_line:
                            genre = genre_line[0].split('GENRE:')[1].strip().lower()
                            break
                    
                    if '"genre":' in content.lower():
                        import re
                        genre_match = re.search(r'"genre":\s*"([^"]+)"', content.lower())
                        if genre_match:
                            genre = genre_match.group(1)
                            break
            
            
            genre_templates = {
                "noir": {
                    "setting": "rain-soaked detective office with venetian blind shadows",
                    "atmosphere": "noir detective atmosphere",
                    "elements": ["venetian blind shadows", "rain", "dim lighting"],
                    "character_desc": "detective in trench coat"
                },
                "scifi": {
                    "setting": "futuristic space station corridor with holographic displays",
                    "atmosphere": "sci-fi futuristic atmosphere",
                    "elements": ["holographic displays", "metallic surfaces", "blue lighting"],
                    "character_desc": "astronaut in advanced suit"
                },
                "horror": {
                    "setting": "abandoned mansion hallway with flickering candles",
                    "atmosphere": "horror gothic atmosphere", 
                    "elements": ["flickering shadows", "dust particles", "eerie lighting"],
                    "character_desc": "figure in dark clothing"
                },
                "fantasy": {
                    "setting": "mystical forest clearing with magical energy",
                    "atmosphere": "fantasy magical atmosphere",
                    "elements": ["magical particles", "ethereal light", "ancient trees"],
                    "character_desc": "wizard with glowing staff"
                },
                "western": {
                    "setting": "dusty main street in frontier town at high noon",
                    "atmosphere": "western frontier atmosphere",
                    "elements": ["dust clouds", "harsh sunlight", "weathered buildings"],
                    "character_desc": "gunslinger in cowboy hat"
                },
                "thriller": {
                    "setting": "urban alleyway with dramatic shadows",
                    "atmosphere": "thriller suspense atmosphere",
                    "elements": ["dramatic shadows", "urban decay", "harsh lighting"],
                    "character_desc": "protagonist in casual clothes"
                },
                "action": {
                    "setting": "industrial warehouse with metal structures",
                    "atmosphere": "action-packed atmosphere",
                    "elements": ["metal structures", "sparks", "dynamic lighting"],
                    "character_desc": "action hero in tactical gear"
                },
                "drama": {
                    "setting": "intimate indoor space with natural lighting",
                    "atmosphere": "dramatic emotional atmosphere",
                    "elements": ["natural lighting", "personal objects", "warm tones"],
                    "character_desc": "character in everyday clothes"
                }
            }
            
            template = genre_templates.get(genre, genre_templates["noir"])
            
            import json
            
            shots = []
            shot_types = ["establishing_wide", "medium", "close_up", "over_shoulder", "medium", "wide"]
            camera_angles = ["eye-level", "low-angle", "eye-level", "high-angle", "dutch-angle", "eye-level"]
            compositions = ["rule-of-thirds", "leading-lines", "centered", "frame-within-frame", "symmetrical", "rule-of-thirds"]
            
            for i in range(6):
                shots.append({
                    "shot_number": i + 1,
                    "shot_type": shot_types[i],
                    "description": f"{shot_types[i].replace('_', ' ').title()} of {template['character_desc']} in {template['setting']}",
                    "camera_angle": camera_angles[i],
                    "camera_movement": "static" if i % 2 == 0 else "tracking",
                    "composition": compositions[i],
                    "duration_seconds": 3.0 + (i * 0.5),
                    "narrative_purpose": f"Shot {i+1}: {template['atmosphere']} progression",
                    "visual_elements": template['elements'] + [f"shot_{i+1}_specific"]
                })
            
            mock_data = {
                "shots": shots,
                "total_shots": 6,
                "estimated_duration": 21.0,
                "visual_style_notes": f"{genre.title()} aesthetic with genre-appropriate visual elements and professional shot progression"
            }
            return json.dumps(mock_data)
        elif "JSONStructuringAgent" in self.name:
            import json
            
            
            genre = "noir"  
            if self.messages:
                
                for message in self.messages:
                    content = message.content
                    if "GENRE:" in content:
                        genre_line = [line for line in content.split('\n') if 'GENRE:' in line]
                        if genre_line:
                            genre = genre_line[0].split('GENRE:')[1].strip().lower()
                            break
                    
                    if '"genre":' in content.lower():
                        import re
                        genre_match = re.search(r'"genre":\s*"([^"]+)"', content.lower())
                        if genre_match:
                            genre = genre_match.group(1)
                            break
            
            
            genre_params = {
                "noir": {
                    "lighting": 25, "color_temp": 3200, "contrast": 75,
                    "prompts": ["noir detective office with venetian blind shadows", "rain-soaked street with neon reflections", "close-up in dramatic shadow lighting"]
                },
                "scifi": {
                    "lighting": 60, "color_temp": 6500, "contrast": 65,
                    "prompts": ["futuristic space station corridor", "holographic interface interaction", "alien technology close-up"]
                },
                "horror": {
                    "lighting": 20, "color_temp": 2800, "contrast": 85,
                    "prompts": ["abandoned mansion hallway", "flickering candlelight scene", "terrifying close-up in shadows"]
                },
                "fantasy": {
                    "lighting": 50, "color_temp": 4500, "contrast": 60,
                    "prompts": ["mystical forest clearing", "magical energy manifestation", "enchanted character portrait"]
                },
                "western": {
                    "lighting": 70, "color_temp": 3800, "contrast": 80,
                    "prompts": ["dusty main street at high noon", "saloon interior with harsh light", "cowboy portrait in desert sun"]
                },
                "action": {
                    "lighting": 65, "color_temp": 5000, "contrast": 75,
                    "prompts": ["industrial warehouse action scene", "dynamic chase sequence", "intense character moment"]
                },
                "thriller": {
                    "lighting": 35, "color_temp": 4000, "contrast": 80,
                    "prompts": ["urban alleyway with dramatic shadows", "tense indoor confrontation", "suspenseful close-up"]
                },
                "drama": {
                    "lighting": 55, "color_temp": 4200, "contrast": 55,
                    "prompts": ["intimate indoor conversation", "emotional character moment", "natural lighting portrait"]
                }
            }
            
            params = genre_params.get(genre, genre_params["noir"])
            
            
            frames = []
            shot_types = ["establishing wide shot", "medium shot", "close-up", "over shoulder shot", "medium tracking shot", "wide closing shot"]
            fovs = [35, 50, 85, 65, 45, 28]
            camera_angles = ["eye-level", "low-angle", "eye-level", "high-angle", "dutch-angle", "eye-level"]
            compositions = ["rule-of-thirds", "leading-lines", "centered", "frame-within-frame", "symmetrical", "rule-of-thirds"]
            
            for i in range(6):
                frames.append({
                    "frame_id": f"frame_{uuid.uuid4().hex[:8]}",
                    "prompt": f"Professional {genre} cinematography, {shot_types[i]}: {params['prompts'][i % len(params['prompts'])]}",
                    "negative_prompt": "blurry, low quality, amateur, oversaturated",
                    "parameters": {
                        "fov": fovs[i],
                        "lighting": params["lighting"] + (i * 5),
                        "hdr_bloom": 60 - (i * 5),
                        "color_temp": params["color_temp"] + (i * 100),
                        "contrast": params["contrast"] + (i * 2),
                        "camera_angle": camera_angles[i],
                        "composition": compositions[i]
                    },
                    "technical_notes": f"{genre.title()} cinematography frame {i+1} with genre-appropriate lighting and color temperature",
                    "consistency_tags": [f"{genre}_appropriate", "professional", "cinematic", f"frame_{i+1}"]
                })
            
            mock_data = {
                "frames": frames,
                "global_consistency": {
                    "lighting_setup": f"{genre} cinematography",
                    "color_palette": f"{genre}-appropriate color grading",
                    "genre": genre,
                    "style": f"professional {genre} filmmaking"
                }
            }
            return json.dumps(mock_data)
        elif "ConsistencyAgent" in self.name:
            return '''{"consistency_analysis": {"overall_score": 92, "character_consistency": 95, "environment_consistency": 90, "lighting_consistency": 88}, "consistency_rules": {"environment": {"weather": "heavy rain", "time_of_day": "night", "location": "cyberpunk street"}}, "issues_detected": [], "corrections": [], "consistency_tags": {"global_tags": ["noir_aesthetic", "cyberpunk_setting", "rainy_night"]}}'''
        elif "RefinementAgent" in self.name:
            return '''{"refinement_analysis": {"feedback_interpretation": "User wants more dramatic lighting", "affected_elements": ["lighting", "contrast"], "change_scope": "single_frame", "consistency_impact": "minor"}, "parameter_changes": [{"frame_id": "frame_001", "parameter": "lighting", "current_value": 60, "new_value": 35, "change_reason": "Reduce lighting for more dramatic effect"}], "prompt_modifications": []}'''
        else:
            return '''{"status": "mock_response", "message": "Agent response simulated - Google API not configured", "agent": "''' + self.name + '''"}'''
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        Args:
            input_data: Agent-specific input data
            
        Returns:
            Agent-specific output data
        """
        pass
    
    def reset_conversation(self) -> None:
        """Reset conversation history to initial state."""
        self.messages = [SystemMessage(content=self.system_prompt)]
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this agent."""
        return {
            "agent_name": self.name,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "message_count": len(self.messages),
        }