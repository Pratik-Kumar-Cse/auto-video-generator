"""
FastAPI Video Generation Service
Main application entry point with comprehensive middleware and configuration
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    CustomHTTPException,
    DatabaseException,
    ValidationException,
)
from app.core.redis_client import close_redis, init_redis
from app.loggers.logger import setup_logger
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityMiddleware
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer()
setup_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting FastAPI Video Generation Service...")

    # Initialize database connection
    await init_db()
    logger.info("Database connection initialized")

    # Initialize Redis connection
    await init_redis()
    logger.info("Redis connection initialized")

    # Initialize Celery
    logger.info("Celery worker initialized")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI Video Generation Service...")

    # Close database connection
    await close_db()
    logger.info("Database connection closed")

    # Close Redis connection
    await close_redis()
    logger.info("Redis connection closed")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="Video Generation API",
        description="AI-powered video generation service with comprehensive features",
        version="1.0.0",
        docs_url="/docs" if settings.ENV == "dev" else None,
        redoc_url="/redoc" if settings.ENV == "dev" else None,
        openapi_url="/openapi.json" if settings.ENV == "dev" else None,
        lifespan=lifespan,
    )

    # # Add security middleware
    # app.add_middleware(SecurityMiddleware)

    # # Add rate limiting middleware
    # app.add_middleware(RateLimitMiddleware)

    # # Add logging middleware
    # app.add_middleware(LoggingMiddleware)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Range", "X-Content-Range"],
        max_age=300,
    )

    # Add trusted host middleware for production
    if settings.ENV == "prod":
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    return app


# Create FastAPI application
app = create_application()


# Custom OpenAPI schema with security
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Video Generation API",
        version="1.0.0",
        description="AI-powered video generation service with comprehensive features",
        routes=app.routes,
    )

    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token in the format: Bearer <token>",
        }
    }

    # Apply security to all endpoints
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method != "options":
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Exception handlers
@app.exception_handler(CustomHTTPException)
async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "code": exc.status_code,
            "error_type": exc.__class__.__name__,
        },
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": "Validation error", "details": exc.detail, "code": 422},
    )


@app.exception_handler(DatabaseException)
async def database_exception_handler(request: Request, exc: DatabaseException):
    logger.error(f"Database error: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Database error occurred", "code": 500},
    )


@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(
    request: Request, exc: AuthenticationException
):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": exc.detail, "code": 401},
    )


@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(
    request: Request, exc: AuthorizationException
):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"message": exc.detail, "code": 403},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "code": 500},
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    if settings.ENV == "prod":
        return {
            "message": "Welcome to the Video Generation API service",
            "version": "1.0.0",
            "status": "running",
        }

    return {
        "message": "Welcome to the Video Generation API service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "/api/v1/health",
            "videos": "/api/v1/videos",
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
        },
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "video-generation-api", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV == "dev",
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.ENV == "dev" else 4,
    )
