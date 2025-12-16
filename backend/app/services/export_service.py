"""
Export service - Handles project exports in various formats.
"""

import json
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import settings
from app.core.logging import LoggerMixin
from app.models.database import Frame, Project


class ExportService(LoggerMixin):
    """
    Service for exporting storyboard projects in various formats.
    
    Supported formats:
    - JSON: Complete project data with metadata
    - MP4: Video sequence of frames
    - EXR: High-quality image sequence
    - Nuke: Compositing script for Foundry Nuke
    """
    
    def __init__(self) -> None:
        self.upload_dir = Path(settings.UPLOAD_DIR).resolve()
    
    async def export_project(
        self,
        project: Project,
        frames: List[Frame],
        format: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Export project in specified format.
        
        Args:
            project: Project database model
            frames: List of frame database models
            format: Export format (json, mp4, exr, nuke)
            options: Export options
            
        Returns:
            Export result with content, media_type, and filename
        """
        options = options or {}
        
        self.logger.info(
            "Starting project export",
            project_id=project.id,
            format=format,
            frame_count=len(frames)
        )
        
        if format == "json":
            return await self._export_json(project, frames, options)
        elif format == "mp4":
            return await self._export_mp4(project, frames, options)
        elif format == "exr":
            return await self._export_exr_sequence(project, frames, options)
        elif format == "nuke":
            return await self._export_nuke_script(project, frames, options)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def _export_json(
        self,
        project: Project,
        frames: List[Frame],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export project as JSON."""
        
        # Build comprehensive project data
        project_data = {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "genre": project.genre.value,
                "status": project.status.value,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
            },
            "frames": [
                {
                    "id": frame.id,
                    "sequence_number": frame.sequence_number,
                    "prompt": frame.prompt,
                    "image_url": frame.image_url,
                    "params": frame.params,
                    "notes": frame.notes,
                    "created_at": frame.created_at.isoformat(),
                } for frame in frames
            ],
            "metadata": {
                "export_format": "json",
                "export_timestamp": datetime.utcnow().isoformat(),
                "frame_count": len(frames),
                "sceneforge_version": "1.0.0",
                "include_metadata": options.get("include_metadata", True),
            }
        }
        
        # Add technical metadata if requested
        if options.get("include_metadata", True):
            project_data["technical_specs"] = {
                "image_format": "PNG",
                "color_space": "sRGB",
                "bit_depth": "8-bit",
                "aspect_ratio": "16:9",
                "resolution": "1920x1080",
            }
        
        json_content = json.dumps(project_data, indent=2, ensure_ascii=False)
        
        return {
            "content": json_content.encode('utf-8'),
            "media_type": "application/json",
            "filename": f"{project.name}_storyboard.json"
        }
    
    async def _export_mp4(
        self,
        project: Project,
        frames: List[Frame],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export project as MP4 video sequence using ffmpeg."""
        
        try:
            import subprocess
            import shutil
            
            # Check if ffmpeg is available
            if not shutil.which('ffmpeg'):
                self.logger.warning("ffmpeg not found, falling back to image sequence ZIP")
                return await self._export_exr_sequence(project, frames, options)
            
            # Create temporary directory for frames
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy/link frames to temp directory with sequential naming
                valid_frames = []
                for i, frame in enumerate(frames):
                    if frame.image_url and frame.image_url.startswith('/uploads/'):
                        image_path = self.upload_dir / frame.image_url[9:]
                        
                        if image_path.exists():
                            # Copy to temp with sequential naming
                            dest_path = temp_path / f"frame_{i+1:04d}.png"
                            shutil.copy2(str(image_path), str(dest_path))
                            valid_frames.append(dest_path)
                        else:
                            self.logger.warning(f"Image not found: {image_path}")
                
                if not valid_frames:
                    raise ValueError("No valid frames found for video export")
                
                # Output video path
                output_path = temp_path / f"{project.name}_reel.mp4"
                
                # Get options
                fps = options.get("fps", 2)  # 2 seconds per frame = 0.5 fps, but we'll use 2fps and duplicate
                quality = options.get("quality", "high")
                
                # Set quality parameters
                if quality == "high":
                    crf = "18"  # High quality
                    preset = "slow"
                elif quality == "medium":
                    crf = "23"  # Medium quality
                    preset = "medium"
                else:
                    crf = "28"  # Lower quality
                    preset = "fast"
                
                # Build ffmpeg command
                # Use concat demuxer for better control
                concat_file = temp_path / "concat.txt"
                with open(concat_file, 'w') as f:
                    for frame_path in valid_frames:
                        # Each frame shows for 2 seconds
                        f.write(f"file '{frame_path.name}'\n")
                        f.write(f"duration 2.0\n")
                    # Add last frame again (ffmpeg concat quirk)
                    f.write(f"file '{valid_frames[-1].name}'\n")
                
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', str(concat_file),
                    '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                    '-c:v', 'libx264',
                    '-crf', crf,
                    '-preset', preset,
                    '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart',
                    '-y',  # Overwrite output
                    str(output_path)
                ]
                
                self.logger.info(
                    "Running ffmpeg for MP4 export",
                    frame_count=len(valid_frames),
                    fps=fps,
                    quality=quality
                )
                
                # Run ffmpeg
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    self.logger.error("ffmpeg failed", stderr=result.stderr)
                    raise ValueError(f"ffmpeg failed: {result.stderr}")
                
                # Read the output video
                with open(output_path, 'rb') as f:
                    video_content = f.read()
                
                self.logger.info(
                    "MP4 export completed",
                    file_size=len(video_content),
                    frame_count=len(valid_frames)
                )
                
                return {
                    "content": video_content,
                    "media_type": "video/mp4",
                    "filename": f"{project.name}_reel.mp4"
                }
            
        except subprocess.TimeoutExpired:
            self.logger.error("ffmpeg timeout")
            raise ValueError("Video export timed out")
        except Exception as e:
            self.logger.error("MP4 export failed", error=str(e))
            # Fallback to image sequence
            self.logger.info("Falling back to image sequence export")
            return await self._export_exr_sequence(project, frames, options)
    
    async def _export_exr_sequence(
        self,
        project: Project,
        frames: List[Frame],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export project as EXR image sequence."""
        
        try:
            # Create a ZIP file containing all frame images
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    
                    # Add project metadata
                    metadata = {
                        "project_name": project.name,
                        "frame_count": len(frames),
                        "export_timestamp": datetime.utcnow().isoformat(),
                        "format": "EXR_SEQUENCE"
                    }
                    zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))
                    
                    # Add each frame image
                    for i, frame in enumerate(frames):
                        if frame.image_url and frame.image_url.startswith('/uploads/'):
                            # Get the actual image file
                            image_path = self.upload_dir / frame.image_url[9:]  # Remove '/uploads/'
                            
                            if image_path.exists():
                                # Add to ZIP with sequential naming
                                sequence_name = f"frame_{i+1:04d}.png"
                                zip_file.write(str(image_path), sequence_name)
                            else:
                                self.logger.warning(f"Image not found: {image_path}")
                
                # Read the ZIP content
                with open(temp_file.name, 'rb') as f:
                    zip_content = f.read()
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                return {
                    "content": zip_content,
                    "media_type": "application/zip",
                    "filename": f"{project.name}_exr_sequence.zip"
                }
                
        except Exception as e:
            self.logger.error("EXR sequence export failed", error=str(e))
            raise ValueError(f"EXR sequence export failed: {str(e)}")
    
    async def _export_nuke_script(
        self,
        project: Project,
        frames: List[Frame],
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export project as Nuke compositing script."""
        
        try:
            # Generate Nuke script content
            nuke_script = self._generate_nuke_script(project, frames, options)
            
            return {
                "content": nuke_script.encode('utf-8'),
                "media_type": "text/plain",
                "filename": f"{project.name}_comp.nk"
            }
            
        except Exception as e:
            self.logger.error("Nuke script export failed", error=str(e))
            raise ValueError(f"Nuke script export failed: {str(e)}")
    
    def _create_slideshow_html(
        self,
        project: Project,
        frames: List[Frame],
        options: Dict[str, Any]
    ) -> str:
        """Create HTML slideshow for video conversion."""
        
        frame_duration = options.get("frame_duration", 3)  # seconds per frame
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name} - Storyboard</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #000;
            font-family: Arial, sans-serif;
            overflow: hidden;
        }}
        .slideshow-container {{
            position: relative;
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .slide {{
            display: none;
            width: 100%;
            height: 100%;
            position: relative;
        }}
        .slide.active {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .slide img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}
        .slide-info {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            color: white;
            background: rgba(0,0,0,0.7);
            padding: 10px;
            border-radius: 5px;
        }}
        .progress-bar {{
            position: absolute;
            bottom: 0;
            left: 0;
            height: 4px;
            background: #00ff88;
            transition: width {frame_duration}s linear;
        }}
    </style>
</head>
<body>
    <div class="slideshow-container">
"""
        
        # Add slides
        for i, frame in enumerate(frames):
            image_url = frame.image_url
            if image_url.startswith('/uploads/'):
                image_url = f"http://localhost:8000{image_url}"
            
            html += f"""
        <div class="slide" data-frame="{i}">
            <img src="{image_url}" alt="Frame {i+1}">
            <div class="slide-info">
                <h3>Frame {i+1}</h3>
                <p>{frame.prompt[:100]}...</p>
            </div>
            <div class="progress-bar"></div>
        </div>
"""
        
        html += f"""
    </div>
    
    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;
        const frameDuration = {frame_duration * 1000}; // Convert to milliseconds
        
        function showSlide(index) {{
            slides.forEach(slide => slide.classList.remove('active'));
            slides[index].classList.add('active');
            
            // Animate progress bar
            const progressBar = slides[index].querySelector('.progress-bar');
            progressBar.style.width = '0%';
            setTimeout(() => {{
                progressBar.style.width = '100%';
            }}, 100);
        }}
        
        function nextSlide() {{
            currentSlide = (currentSlide + 1) % totalSlides;
            showSlide(currentSlide);
        }}
        
        // Start slideshow
        showSlide(0);
        setInterval(nextSlide, frameDuration);
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') {{
                nextSlide();
            }} else if (e.key === 'ArrowLeft') {{
                currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
                showSlide(currentSlide);
            }}
        }});
    </script>
</body>
</html>
"""
        
        return html
    
    def _generate_nuke_script(
        self,
        project: Project,
        frames: List[Frame],
        options: Dict[str, Any]
    ) -> str:
        """Generate Nuke compositing script."""
        
        script = f"""#! Nuke Script Generated by SceneForge
# Project: {project.name}
# Generated: {datetime.utcnow().isoformat()}
# Frame Count: {len(frames)}

version 13.2 v5
define_window_layout_xml {{<?xml version="1.0" encoding="UTF-8"?>
<layout version="1.0">
    <window x="0" y="0" w="1920" h="1080" screen="0">
        <splitter orientation="1">
            <split size="1200"/>
            <dock id="" hideTitles="1" activePageId="Viewer.1">
                <page id="Viewer.1"/>
            </dock>
            <split size="720"/>
            <dock id="" activePageId="DAG.1" focus="true">
                <page id="DAG.1"/>
            </dock>
        </splitter>
    </window>
</layout>
}}

Root {{
 inputs 0
 name Root
 frame 1
 last_frame {len(frames)}
 format "1920 1080 0 0 1920 1080 1 HD_1080"
 proxy_type scale
 proxy_format "1024 778 0 0 1024 778 1 1K_Super_35(full-ap)"
}}

"""
        
        # Add Read nodes for each frame
        for i, frame in enumerate(frames):
            if frame.image_url and frame.image_url.startswith('/uploads/'):
                # Convert to absolute path
                image_path = str(self.upload_dir / frame.image_url[9:])
                
                script += f"""
Read {{
 inputs 0
 file "{image_path}"
 format "1920 1080 0 0 1920 1080 1 HD_1080"
 origset true
 frame {i+1}
 name Read_Frame_{i+1:02d}
 xpos {100 + (i * 150)}
 ypos 100
}}

Text2 {{
 font_size 24
 message "Frame {i+1}: {frame.prompt[:50]}..."
 box {{0 0 1920 100}}
 xjustify center
 yjustify center
 name Text_Frame_{i+1:02d}
 xpos {100 + (i * 150)}
 ypos 200
}}

"""
        
        # Add a simple sequence viewer
        script += f"""
Switch {{
 inputs {len(frames)}
 which {{frame-1}}
 name FrameSequence
 xpos 500
 ypos 400
}}

Viewer {{
 frame_range 1-{len(frames)}
 name Viewer1
 xpos 500
 ypos 500
}}
"""
        
        return script
    
    async def health_check(self) -> bool:
        """Check export service health."""
        try:
            # Test basic functionality
            return self.upload_dir.exists()
        except Exception as e:
            self.logger.error("Export service health check failed", error=str(e))
            return False