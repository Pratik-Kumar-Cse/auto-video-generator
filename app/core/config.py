"""
Configuration management for FastAPI Video Generation Service
Handles environment variables and application settings
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable management"""
    
    # Application settings
    APP_NAME: str = "Video Generation API"
    VERSION: str = "1.0.0"
    ENV: str = Field(default="dev", description="Environment: dev, staging, prod")
    DEBUG: bool = Field(default=True)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")
    
    # Security settings
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    ALGORITHM: str = Field(default="HS256")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed hosts for production"
    )
    
    # Database settings
    MONGO_URI: str = Field(..., description="MongoDB connection URI")
    DATABASE_NAME: str = Field(default="video_generator")
    MONGO_DB_NAME: Optional[str] = Field(default=None)  # Legacy field name
    
    # Redis settings
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    REDIS_URL: Optional[str] = Field(default=None)
    
    # Celery settings
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery result backend")
    CELERY_TASK_SERIALIZER: str = Field(default="json")
    CELERY_RESULT_SERIALIZER: str = Field(default="json")
    CELERY_ACCEPT_CONTENT: List[str] = Field(default=["json"])
    CELERY_TIMEZONE: str = Field(default="UTC")
    CELERY_ENABLE_UTC: bool = Field(default=True)
    
    # AI/ML API Keys
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    CLAUDE_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    REPLICATE_API_TOKEN: Optional[str] = Field(default=None)
    
    # External service API keys
    TAVUS_API_KEY: Optional[str] = Field(default=None)
    HEYGEN_API_KEY: Optional[str] = Field(default=None)
    PEXELS_API_KEY: Optional[str] = Field(default=None)
    STORYBLOCKS_API_KEY: Optional[str] = Field(default=None)
    STORYBLOCKS_SECRET_KEY: Optional[str] = Field(default=None)
    ASSEMBLY_AI_API_KEY: Optional[str] = Field(default=None)
    LEONARDO_API_KEY: Optional[str] = Field(default=None)
    
    # AWS settings
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_REGION: str = Field(default="us-east-1")
    S3_BUCKET_NAME: Optional[str] = Field(default=None)
    AWS_BASE_URL: Optional[str] = Field(default=None)
    
    # Google settings
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None)
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None)
    GOOGLE_CONSOLE_API_KEY: Optional[str] = Field(default=None)
    
    # Social media integration
    YOUTUBE_REDIRECT_URI: Optional[str] = Field(default=None)
    LINKEDIN_CLIENT_ID: Optional[str] = Field(default=None)
    LINKEDIN_CLIENT_SECRET: Optional[str] = Field(default=None)
    LINKEDIN_CALLBACK_URL: Optional[str] = Field(default=None)
    
    # Email settings
    EMAIL_ID: Optional[str] = Field(default=None)
    EMAIL_PASSWORD: Optional[str] = Field(default=None)
    EMAIL_SUBSTRING: Optional[str] = Field(default=None)
    
    # Payment settings
    STRIPE_PRIVATE_KEY: Optional[str] = Field(default=None)
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_BURST: int = Field(default=100)
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024)  # 100MB
    MAX_UPLOAD_SIZE: Optional[str] = Field(default=None)  # Legacy field name
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["mp4", "avi", "mov", "mkv", "webm", "mp3", "wav", "aac"]
    )
    
    # Testing settings
    TESTING: bool = Field(default=False)
    
    # Video processing settings
    DEFAULT_VIDEO_QUALITY: str = Field(default="720p")
    SUPPORTED_VIDEO_QUALITIES: List[str] = Field(default=["720p", "1080p"])
    VIDEO_PROCESSING_TIMEOUT: int = Field(default=3600)  # 1 hour
    
    # Webhook settings
    WEBHOOK_ENDPOINT: Optional[str] = Field(default=None)
    WEBHOOK_SECRET: Optional[str] = Field(default=None)
    
    # Analytics
    MIXPANEL_TOKEN: Optional[str] = Field(default=None)
    MIXPANEL_SECRET: Optional[str] = Field(default=None)
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None)
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("REDIS_URL", pre=True)
    def build_redis_url(cls, v, values):
        if v:
            return v
        
        password = values.get("REDIS_PASSWORD")
        host = values.get("REDIS_HOST", "localhost")
        port = values.get("REDIS_PORT", 6379)
        db = values.get("REDIS_DB", 0)
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"
    
    @property
    def database_url(self) -> str:
        """Get the complete database URL"""
        return self.MONGO_URI
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENV == "dev"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENV == "prod"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in environment


# Create settings instance
settings = Settings()

# Validate critical settings for production
if settings.is_production:
    critical_settings = [
        "SECRET_KEY",
        "MONGO_URI",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "OPENAI_API_KEY"
    ]
    
    missing_settings = []
    for setting in critical_settings:
        if not getattr(settings, setting, None):
            missing_settings.append(setting)
    
    if missing_settings:
        raise ValueError(
            f"Missing critical settings for production: {', '.join(missing_settings)}"
        )