"""
API v1 router setup
"""

from fastapi import APIRouter

from app.api.v1.endpoints import videos, scripts, sse, events

# Create API v1 router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])

api_router.include_router(scripts.router, prefix="/scripts", tags=["scripts"])

api_router.include_router(sse.router, prefix="/sse", tags=["sse"])

api_router.include_router(events.router, prefix="/events", tags=["events"])


# Health check endpoint
@api_router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Video Generator API is running",
        "version": "1.0.0",
    }


# API info endpoint
@api_router.get("/info", tags=["info"])
async def api_info():
    """API information endpoint"""
    return {
        "name": "Video Generator API",
        "version": "1.0.0",
        "description": "FastAPI-based video generation service",
        "endpoints": {
            "videos": "/api/v1/videos",
            "scripts": "/api/v1/scripts",
            "sse": "/api/v1/sse",
            "events": "/api/v1/events",
            "script-events": "/api/v1/events/script-generation",
            "video-events": "/api/v1/events/video-generation",
            "health": "/api/v1/health",
            "docs": "/docs",
            "redoc": "/redoc",
        },
    }
