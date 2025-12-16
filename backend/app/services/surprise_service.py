"""
Surprise service - Uses Gemini AI to generate creative scene suggestions.
"""

import asyncio
import json
import random
from typing import Any, Dict, List

from app.core.config import settings
from app.core.logging import LoggerMixin
from app.models.schemas import Genre


class SurpriseService(LoggerMixin):
    """
    Service for generating creative scene suggestions using Gemini AI.
    
    Features:
    - Creative scene description generation
    - Genre-appropriate parameter suggestions
    - Style-aware cinematography recommendations
    - Fallback to curated suggestions if AI unavailable
    """
    
    def __init__(self) -> None:
        self.creative_templates = {
            "noir": [
                "A mysterious figure in a fedora walks through rain-soaked streets",
                "Smoke curls from a cigarette in a dimly lit detective's office",
                "Shadows dance across venetian blinds as footsteps echo in the hallway",
                "A femme fatale emerges from the fog at midnight",
                "Neon signs reflect in puddles on empty city streets"
            ],
            "scifi": [
                "A lone astronaut discovers an ancient alien artifact",
                "Holographic displays flicker in a futuristic command center",
                "A spaceship approaches a mysterious planet with twin moons",
                "Robots patrol the corridors of an abandoned space station",
                "Energy beams pierce through the darkness of deep space"
            ],
            "horror": [
                "A creaking door slowly opens in an abandoned mansion",
                "Shadows move independently in the flickering candlelight",
                "Fog rolls across an ancient cemetery at midnight",
                "A figure watches from the window of a haunted house",
                "Strange symbols glow on the walls of a dark ritual chamber"
            ],
            "action": [
                "An explosion erupts behind a running figure",
                "A motorcycle chase winds through narrow city streets",
                "Sparks fly as metal clashes against metal in combat",
                "A helicopter hovers over a rooftop pursuit",
                "Bullets shatter glass in a high-speed gunfight"
            ],
            "fantasy": [
                "A dragon soars over misty mountain peaks",
                "Ancient runes glow with magical energy in a forgotten temple",
                "A wizard conjures swirling portals of mystical light",
                "Ethereal creatures dance in an enchanted forest",
                "A knight stands before a towering castle gate"
            ],
            "western": [
                "A lone gunslinger walks down a dusty main street",
                "Tumbleweeds roll past a weathered saloon",
                "A stagecoach races across the desert landscape",
                "Smoke rises from a campfire under the starlit sky",
                "A sheriff's badge glints in the harsh desert sun"
            ]
        }
        
        self.parameter_styles = {
            "dramatic": {
                "fov": (24, 50),
                "lighting": (20, 40),
                "hdrBloom": (40, 80),
                "contrast": (60, 85),
                "colorTemp": (2700, 4000)
            },
            "cinematic": {
                "fov": (35, 85),
                "lighting": (30, 70),
                "hdrBloom": (20, 60),
                "contrast": (45, 75),
                "colorTemp": (3200, 6500)
            },
            "ethereal": {
                "fov": (50, 120),
                "lighting": (60, 90),
                "hdrBloom": (60, 100),
                "contrast": (30, 60),
                "colorTemp": (5000, 8000)
            }
        }
    
    async def generate_creative_scene(
        self,
        current_genre: str = "noir",
        style_preference: str = "cinematic"
    ) -> Dict[str, Any]:
        """
        Generate creative scene suggestion using Gemini AI.
        
        Args:
            current_genre: Current selected genre
            style_preference: Visual style preference
            
        Returns:
            Creative scene suggestion with parameters
        """
        try:
            # Try to use Gemini AI for creative generation
            if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "":
                return await self._generate_with_gemini(current_genre, style_preference)
            else:
                self.logger.warning("Google API key not configured, using curated suggestions")
                return self._generate_curated_suggestion(current_genre, style_preference)
                
        except Exception as e:
            self.logger.error("Failed to generate creative scene with AI", error=str(e))
            return self._generate_curated_suggestion(current_genre, style_preference)
    
    async def _generate_with_gemini(
        self,
        current_genre: str,
        style_preference: str
    ) -> Dict[str, Any]:
        """Generate creative scene using Gemini AI."""
        try:
            import google.generativeai as genai
            
            # Configure Gemini
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            # Create creative prompt for Gemini
            prompt = f"""
            You are a creative director for a {current_genre} film with {style_preference} visual style.
            
            Generate a unique, visually striking scene description that would make an excellent storyboard frame.
            The scene should be:
            - Highly visual and cinematic
            - Appropriate for {current_genre} genre
            - Rich in atmospheric details
            - Suitable for {style_preference} cinematography
            
            Also suggest appropriate camera parameters:
            - Field of view (24-120 degrees)
            - Lighting intensity (0-100%)
            - HDR bloom (0-100%)
            - Color temperature (2700-10000K)
            - Contrast (0-100%)
            - Camera angle (eye-level, low-angle, high-angle, dutch-angle, birds-eye, worms-eye)
            - Composition (rule-of-thirds, centered, leading-lines, symmetrical)
            
            Respond in JSON format:
            {{
                "scene_description": "detailed scene description",
                "genre": "{current_genre}",
                "suggested_params": {{
                    "fov": number,
                    "lighting": number,
                    "hdrBloom": number,
                    "colorTemp": number,
                    "contrast": number,
                    "cameraAngle": "string",
                    "composition": "string"
                }}
            }}
            """
            
            # Generate with Gemini
            response = model.generate_content(prompt)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]
                
                result = json.loads(response_text)
                
                # Validate and sanitize the response
                return self._validate_gemini_response(result, current_genre, style_preference)
                
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse Gemini JSON response, using curated suggestion")
                return self._generate_curated_suggestion(current_genre, style_preference)
                
        except Exception as e:
            self.logger.error("Gemini AI generation failed", error=str(e))
            return self._generate_curated_suggestion(current_genre, style_preference)
    
    def _validate_gemini_response(
        self,
        response: Dict[str, Any],
        fallback_genre: str,
        style_preference: str
    ) -> Dict[str, Any]:
        """Validate and sanitize Gemini response."""
        try:
            # Ensure required fields exist
            scene_description = response.get("scene_description", "")
            if not scene_description or len(scene_description) < 20:
                raise ValueError("Invalid scene description")
            
            # Validate genre
            genre = response.get("genre", fallback_genre)
            valid_genres = [g.value for g in Genre]
            if genre not in valid_genres:
                genre = fallback_genre
            
            # Validate parameters
            params = response.get("suggested_params", {})
            validated_params = {
                "fov": max(24, min(120, params.get("fov", 50))),
                "lighting": max(0, min(100, params.get("lighting", 50))),
                "hdrBloom": max(0, min(100, params.get("hdrBloom", 30))),
                "colorTemp": max(2700, min(10000, params.get("colorTemp", 5500))),
                "contrast": max(0, min(100, params.get("contrast", 50))),
                "cameraAngle": params.get("cameraAngle", "eye-level"),
                "composition": params.get("composition", "rule-of-thirds")
            }
            
            return {
                "scene_description": scene_description,
                "genre": genre,
                "suggested_params": validated_params
            }
            
        except Exception as e:
            self.logger.error("Failed to validate Gemini response", error=str(e))
            return self._generate_curated_suggestion(fallback_genre, style_preference)
    
    def _generate_curated_suggestion(
        self,
        genre: str,
        style_preference: str
    ) -> Dict[str, Any]:
        """Generate curated creative suggestion as fallback."""
        
        # Get genre templates
        templates = self.creative_templates.get(genre, self.creative_templates["noir"])
        base_scene = random.choice(templates)
        
        # Add creative variations
        variations = [
            "bathed in ethereal moonlight",
            "with dramatic chiaroscuro lighting",
            "as storm clouds gather overhead",
            "reflected in shattered mirrors",
            "through swirling mist and fog",
            "with sparks of magical energy",
            "under the glow of neon signs",
            "as shadows dance on ancient walls"
        ]
        
        enhanced_scene = f"{base_scene} {random.choice(variations)}"
        
        # Generate style-appropriate parameters
        style_ranges = self.parameter_styles.get(style_preference, self.parameter_styles["cinematic"])
        
        suggested_params = {
            "fov": random.randint(*style_ranges["fov"]),
            "lighting": random.randint(*style_ranges["lighting"]),
            "hdrBloom": random.randint(*style_ranges["hdrBloom"]),
            "colorTemp": random.randint(*style_ranges["colorTemp"]),
            "contrast": random.randint(*style_ranges["contrast"]),
            "cameraAngle": random.choice(["eye-level", "low-angle", "high-angle", "dutch-angle"]),
            "composition": random.choice(["rule-of-thirds", "centered", "leading-lines", "symmetrical"])
        }
        
        return {
            "scene_description": enhanced_scene,
            "genre": genre,
            "suggested_params": suggested_params
        }
    
    async def health_check(self) -> bool:
        """Check if surprise service is healthy."""
        try:
            # Test curated generation
            result = self._generate_curated_suggestion("noir", "cinematic")
            return bool(result.get("scene_description"))
        except Exception as e:
            self.logger.error("Surprise service health check failed", error=str(e))
            return False