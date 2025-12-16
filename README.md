# SceneForge 🎬

> **Professional AI-Powered Storyboard Generation Platform**  
> Transform scene descriptions into production-ready HDR storyboards with cinematic precision.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)

---

## 🌟 Overview

**SceneForge** is an enterprise-grade platform that leverages cutting-edge AI to generate professional storyboards from natural language descriptions. Built for filmmakers, VFX artists, and creative professionals, it combines multi-agent AI orchestration with Bria's FIBO API to deliver production-ready HDR frames with precise technical parameters.

### Key Features

- 🤖 **Multi-Agent AI System** - Orchestrated agents for scene analysis, parameter generation, and consistency
- 🎨 **Professional HDR Generation** - Bria FIBO integration for cinematic-quality 16-bit frames
- 🎬 **Cinematic Parameter Control** - FOV, lighting, HDR bloom, color temperature, camera angles
- ⚡ **Real-Time Progress Tracking** - Live updates through WebSocket-style polling
- 🔄 **Frame Refinement** - AI-powered iterative improvements using Bria V2 API
- 📤 **Multi-Format Export** - EXR sequences, MP4 reels, Nuke scripts, JSON parameters
- 🎭 **Genre-Aware Generation** - Optimized for Noir, Sci-Fi, Horror, Action, and more
- 🔗 **Shareable Projects** - Time-limited public links with view tracking
- 🎮 **Demo Mode** - Full-featured demo with mock data for testing

---

## 🏗️ Architecture

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Vite for blazing-fast builds
- TailwindCSS + shadcn/ui for modern UI
- Zustand for state management
- Framer Motion for animations
- React DnD Kit for timeline interactions

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy with SQLite/PostgreSQL
- Pydantic for data validation
- Gemini Model for AI agents
- Bria FIBO API for image generation
- Async/await throughout

**AI Architecture:**
- **Orchestrator Agent** - Coordinates multi-agent workflow
- **Script Breakdown Agent** - Analyzes narrative structure
- **JSON Structuring Agent** - Converts to technical parameters
- **Consistency Agent** - Ensures visual coherence
- **Refinement Agent** - Iterative improvements

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ and npm/yarn
- **Python** 3.11+
- **OpenAI API Key** (for AI agents)
- **Bria API Key** (for image generation)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/justinDevel/sceneforge.git
cd sceneforge
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
# GOOGLE_API_KEY=your_gemini_key
# BRIA_API_KEY=your_bria_key

# Initialize database
python -c "from app.models.database import init_db; init_db()"

# Run backend
python run.py
```

Backend will start on `http://localhost:8000`

#### 3. Frontend Setup

```bash
# From project root
npm install

# Start development server
npm run dev
```

Frontend will start on `http://localhost:5173`

### Docker Setup (Alternative)

```bash
cd backend
docker-compose up -d
```

---

## 📖 Usage Guide

### Basic Workflow

1. **Describe Your Scene**
   - Enter a detailed scene description
   - Select genre (Noir, Sci-Fi, Horror, etc.)
   - Adjust base parameters (FOV, lighting, HDR)

2. **Generate Storyboard**
   - Click "Generate Storyboard"
   - Watch real-time progress through 5 AI stages
   - Review generated frames in timeline

3. **Refine Frames**
   - Click sparkle icon on any frame
   - Describe desired changes
   - AI refines while maintaining consistency

4. **Export & Share**
   - Export as EXR, MP4, Nuke script, or JSON
   - Create shareable links (30-day expiry)
   - Download production-ready files

### Demo Mode

Toggle **Demo Mode** in the header to:
- Test full functionality without API keys
- Use mock data and sample images
- Explore UI/UX without costs
- Perfect for development and demos

### API Endpoints

**Generation:**
- `POST /api/v1/generation/generate` - Start storyboard generation
- `POST /api/v1/generation/refine` - Refine specific frame
- `GET /api/v1/generation/jobs/{job_id}` - Poll job status

**Projects:**
- `GET /api/v1/generation/projects` - List projects
- `GET /api/v1/generation/projects/{id}` - Get project details
- `POST /api/v1/generation/projects` - Create project

**Export & Share:**
- `POST /api/v1/generation/export/{id}` - Export project
- `POST /api/v1/generation/share/{id}` - Create share link
- `GET /api/v1/generation/share/{token}` - Access shared project

**Utilities:**
- `POST /api/v1/generation/surprise-me` - AI-generated creative prompts
- `GET /api/v1/health` - Health check

---

## 🎨 Features Deep Dive

### Multi-Agent AI System

SceneForge uses a sophisticated multi-agent architecture:

1. **Script Breakdown** - Analyzes narrative beats and key moments
2. **JSON Structuring** - Converts creative descriptions to technical parameters
3. **Consistency Check** - Ensures visual coherence across frames
4. **Image Generation** - Bria FIBO creates HDR frames
5. **Refinement** - Iterative improvements based on feedback

### Technical Parameters

Each frame includes precise control over:

- **Camera:** FOV (10-120°), angle (8 presets), composition rules
- **Lighting:** Intensity (0-100%), color temperature (2000-10000K)
- **HDR:** Bloom intensity, contrast, dynamic range
- **Style:** Genre-specific presets and custom adjustments

### Export Formats

- **EXR Sequence** - 16-bit HDR frames for VFX pipelines
- **MP4 Reel** - Video preview with timing
- **Nuke Script** - Compositing project with nodes
- **JSON Parameters** - Complete technical specifications

---

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
# API Keys
OPENAI_API_KEY=sk-...
BRIA_API_KEY=...
BRIA_API_URL=https://engine.prod.bria-api.com/v1

# Database
DATABASE_URL=sqlite:///./sceneforge.db
# Or PostgreSQL: postgresql://user:pass@localhost/sceneforge

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760

# Security
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**Frontend (vite.config.ts):**
```typescript
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest test_basic.py

# Run with coverage
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
# Run unit tests
npm test

# Run E2E tests
npm run test:e2e

# Type checking
npm run type-check
```

---

## 📦 Deployment

### Production Build

**Frontend:**
```bash
npm run build
# Output in dist/
```

**Backend:**
```bash
# Use gunicorn for production
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Checklist

- [ ] Set `DEBUG=false`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper CORS origins
- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Set up CDN for static assets
- [ ] Configure backup strategy
- [ ] Set up monitoring (Sentry, etc.)

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow TypeScript/Python best practices
- Write tests for new features
- Update documentation
- Use conventional commits
- Ensure CI passes

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Bria AI** - Professional image generation API
- **Gemini** - Gemini model for multi-agent orchestration
- **shadcn/ui** - Beautiful UI components
- **FastAPI** - Modern Python web framework

---

## 📞 Support

- **Documentation:** [docs.sceneforge.ai](https://docs.sceneforge.ai)
- **Issues:** [GitHub Issues](https://github.com/yourusername/sceneforge/issues)
- **Discord:** [Join our community](https://discord.gg/sceneforge)
- **Email:** support@sceneforge.ai

---

## 🗺️ Roadmap

- [ ] Real-time collaboration
- [ ] Video-to-storyboard conversion
- [ ] Custom AI model training
- [ ] Blender/Maya integration
- [ ] Mobile app (iOS/Android)
- [ ] Cloud rendering service
- [ ] Team workspaces
- [ ] Version control for projects

---

<div align="center">

**Built with ❤️ by the SceneForge Team**

[Website](https://sceneforge.ai) • [Documentation](https://docs.sceneforge.ai) • [Twitter](https://twitter.com/sceneforge)

</div>
