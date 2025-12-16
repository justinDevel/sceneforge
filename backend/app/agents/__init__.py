"""
AI Agents for SceneForge - Agentic Pre-Vis Pipeline.

This module contains specialized AI agents that collaborate to transform
high-level scene descriptions into professional pre-visualization storyboards.

Agents:
- ScriptBreakdownAgent: Parses scene descriptions into individual shots
- JSONStructuringAgent: Converts natural language to precise JSON parameters  
- ConsistencyAgent: Ensures continuity across multiple frames
- RefinementAgent: Handles user feedback and iterative improvements
"""

from .script_breakdown import ScriptBreakdownAgent
from .json_structuring import JSONStructuringAgent
from .consistency import ConsistencyAgent
from .refinement import RefinementAgent
from .orchestrator import AgentOrchestrator

__all__ = [
    "ScriptBreakdownAgent",
    "JSONStructuringAgent", 
    "ConsistencyAgent",
    "RefinementAgent",
    "AgentOrchestrator",
]