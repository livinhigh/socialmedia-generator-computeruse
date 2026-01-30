"""
FastAPI application for Social Media Post Generator.
Follows SOLID principles with clear separation of concerns.

Architecture:
- Routes: Endpoint handlers for post creation and management
- Services: Business logic for post generation and Gemini automation
- Database: SQLAlchemy ORM for persistence
- Schemas: Pydantic models for request/response validation

New Features:
- Create posts with multiple data sources (text/links)
- Real-time WebSocket updates during generation
- Google Gemini integration for text and image generation
- Variation selection and management
"""

import os
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from socialmedia_generator.database import init_db

# ============================================================================
# Logging Configuration
# ============================================================================

# Configure logging to stdout for Docker
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import routers - NEW: Only posts router for social media generation
from socialmedia_generator.routes import posts


# ============================================================================
# Application Initialization
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup/shutdown.
    Follows Single Responsibility Principle by handling resource management.
    """
    # Startup
    logger.info("🚀 Social Media Post Generator API starting up...")
    init_db()  # Initialize database
    
    # Shutdown
    yield
    logger.info("🛑 Social Media Post Generator API shutting down...")


app = FastAPI(
    title="Social Media Post Generator API",
    description="AI-powered social media content generation using Google Gemini",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Register Route Handlers
# ============================================================================

# NEW: Only social media post routes
app.include_router(posts.router)


# ============================================================================
# Static Files & Frontend
# ============================================================================

# Mount static files directory for frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """API information and available endpoints."""
    # Serve frontend `index.html` if present in the mounted static directory
    index_path = os.path.join(static_dir, "generator.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")

    return {
        "name": "Social Media Post Generator API",
        "version": "2.0.0",
        "description": "AI-powered social media content generation using Google Gemini",
        "endpoints": {
            "create_post": "POST /api/posts",
            "get_post": "GET /api/posts/{post_id}",
            "websocket_updates": "WS /api/posts/{post_id}/updates",
            "select_variations": "POST /api/posts/{post_id}/select",
            "publish_post": "POST /api/posts/{post_id}/publish (placeholder)",
            "docs": "/docs"
        },
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError with proper HTTP response."""
    from fastapi import HTTPException
    raise HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
