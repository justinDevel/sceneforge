#!/usr/bin/env python3
"""
Basic test to verify SceneForge backend functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_basic_functionality():
    """Test basic backend functionality."""
    print("🧪 Testing SceneForge Backend...")
    
    # Set minimal environment
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-32-characters-long")
    os.environ.setdefault("BRIA_API_KEY", "test-key")
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    os.environ.setdefault("DEBUG", "true")
    
    try:
        # Test imports
        print("✅ Testing imports...")
        from app.core.config import settings
        from app.core.logging import configure_logging, get_logger
        from app.models.schemas import SceneGenerationRequest, Genre, FrameParams
        from app.agents.orchestrator import AgentOrchestrator
        from app.services.bria_client import BriaClient
        from app.database import create_tables
        
        print(f"✅ Configuration loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
        
        # Test logging
        print("✅ Testing logging...")
        configure_logging()
        logger = get_logger("test")
        logger.info("Test log message")
        
        # Test database
        print("✅ Testing database...")
        create_tables()
        
        # Test schemas
        print("✅ Testing schemas...")
        request = SceneGenerationRequest(
            scene_description="A test scene with dramatic lighting",
            genre=Genre.NOIR,
            frame_count=3,
            base_params=FrameParams(
                fov=35,
                lighting=60,
                hdr_bloom=40,
                color_temp=3200,
                contrast=70,
                camera_angle="low-angle",
                composition="rule-of-thirds"
            )
        )
        print(f"✅ Request created: {request.scene_description[:30]}...")
        
        # Test agent orchestrator (without actual API calls)
        print("✅ Testing agent orchestrator...")
        try:
            from app.agents.orchestrator import AgentOrchestrator
            print("✅ Orchestrator class imported successfully")
        except Exception as e:
            print(f"⚠️  Orchestrator import warning: {e}")
            print("✅ This is expected without proper OpenAI configuration")
        
        print("\n🎉 All basic tests passed!")
        print("🚀 Backend is ready for development")
        print("\nNext steps:")
        print("1. Set your BRIA_API_KEY and OPENAI_API_KEY in .env")
        print("2. Run: python run.py")
        print("3. Visit: http://localhost:8000/docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    sys.exit(0 if success else 1)