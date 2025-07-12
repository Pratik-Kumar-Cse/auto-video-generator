"""
Configuration management for FastAPI Video Generation Service
Handles environment variables and application settings
"""

import warnings
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, ValidationError, validator
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module="moviepy")
warnings.filterwarnings(
    "ignore", message="invalid escape sequence", category=SyntaxWarning
)


class Settings(BaseSettings):
    """Application settings with environment variable management"""

    # Application settings
    APP_NAME: str = Field(default="Video Generation API")
    VERSION: str = Field(default="1.0.0")
    ENV: str = Field(default="dev", description="Environment: dev, staging, prod")
    DEBUG: bool = Field(default=True)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    LOG_LEVEL: str = Field(default="INFO")
    ORIGIN: str = Field(default="*")
    DOMAIN: str = Field(default="localhost")
    FRONTEND_ENDPOINT: str = Field(default="http://localhost:3000")
    API_GATEWAY_URL: str = Field(default="")

    # Security settings
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    TOKEN_EXPIRY_IN_HOUR: int = Field(default=24)
    LOGIN_EXPIRE_TIME: int = Field(default=30)
    REFRESH_EXPIRE_TIME: int = Field(default=7)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    ALGORITHM: str = Field(default="HS256")
    USER_JWT_COOKIE: str = Field(default="access_token")
    LOGIN_URL: str = Field(default="/auth/login")

    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins",
    )
    API_CORS_ORIGINS: str = Field(default="*")
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"], description="Allowed hosts for production"
    )

    # Database settings
    MONGO_URI: str = Field(..., description="MongoDB connection URI")
    DATABASE_NAME: str = Field(default="video_generator")

    # Redis settings
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: str = Field(default="6379")
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    REDIS_URL: Optional[str] = Field(default=None)
    CACHE_PROVIDER: str = Field(default="redis")

    # Celery settings
    CELERY_BROKER_URL: Optional[str] = Field(
        default=None, description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: Optional[str] = Field(
        default=None, description="Celery result backend"
    )
    CELERY_BACKEND_URL: Optional[str] = Field(default=None)  # Alternative name
    # RABBITMQ_BROKER_URL: Optional[str] = Field(default=None)
    CELERY_TASK_SERIALIZER: str = Field(default="json")
    CELERY_RESULT_SERIALIZER: str = Field(default="json")
    CELERY_ACCEPT_CONTENT: List[str] = Field(default=["json"])
    CELERY_TIMEZONE: str = Field(default="UTC")
    CELERY_ENABLE_UTC: bool = Field(default=True)

    # AI/ML API Keys
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    REQUESTY_KEY: Optional[str] = Field(default=None, description="Requesty API key")
    CLAUDE_API_KEY: Optional[str] = Field(default=None)
    CLAUDE_KEY: Optional[str] = Field(default=None)  # Alternative name
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    REPLICATE_API_TOKEN: Optional[str] = Field(default=None)
    DEEPSEEK_API: Optional[str] = Field(default=None)

    # External service API keys
    TAVUS_API_KEY: Optional[str] = Field(default=None)
    HEYGEN_API_KEY: Optional[str] = Field(default=None)
    PEXELS_API_KEY: Optional[str] = Field(default=None)
    STORYBLOCKS_API_KEY: Optional[str] = Field(default=None)
    STORYBLOCKS_SECRET_KEY: Optional[str] = Field(default=None)
    STORYBLOCKS_SCRECT_KEY: Optional[str] = Field(default=None)  # Typo in original
    ASSEMBLY_AI_API_KEY: Optional[str] = Field(default=None)
    LEONARDO_API_KEY: Optional[str] = Field(default=None)
    SERPER_API_KEY: Optional[str] = Field(default=None)
    TAVILY_API_KEY: Optional[str] = Field(default=None)
    SUTTERSTOCK_TOKEN: Optional[str] = Field(default=None)
    FREEPIK_API_KEY: Optional[str] = Field(default=None)
    GETTY_IMAGES_API_KEY: Optional[str] = Field(default=None)
    WEBSHARE_PROXY_API: Optional[str] = Field(default=None)

    EXA_API_KEY: Optional[str] = Field(default=None)

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
    REDIRECT_URI: Optional[str] = Field(default=None)

    # Social media integration
    YOUTUBE_REDIRECT_URI: Optional[str] = Field(default=None)
    LINKEDIN_CLIENT_ID: Optional[str] = Field(default=None)
    LINKEDIN_CLIENT_SECRET: Optional[str] = Field(default=None)
    LINKEDIN_CALLBACK_URL: Optional[str] = Field(default=None)
    META_CLIENT_ID: Optional[str] = Field(default=None)
    META_CLIENT_SECRET: Optional[str] = Field(default=None)
    META_REDIRECT_URI: Optional[str] = Field(default=None)

    # Email settings
    EMAIL_ID: Optional[str] = Field(default=None)
    EMAIL_PASSWORD: Optional[str] = Field(default=None)
    EMAIL_SUBSTRING: Optional[str] = Field(default=None)

    # Rate limiting
    RATE_LIMIT: str = Field(default="100/minute")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_BURST: int = Field(default=100)

    # File upload settings
    MAX_FILE_SIZE: int = Field(default=100 * 1024 * 1024)  # 100MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["mp4", "avi", "mov", "mkv", "webm", "mp3", "wav", "aac"]
    )

    # Video processing settings
    DEFAULT_VIDEO_QUALITY: str = Field(default="720p")
    SUPPORTED_VIDEO_QUALITIES: List[str] = Field(default=["720p", "1080p"])
    VIDEO_PROCESSING_TIMEOUT: int = Field(default=3600)  # 1 hour
    IMAGEMAGICK_BINARY: str = Field(default="convert")

    # Webhook settings
    WEBHOOK_ENDPOINT: Optional[str] = Field(default=None)
    WEBHOOK_SECRET: Optional[str] = Field(default=None)

    # Analytics and Monitoring
    MIXPANEL_TOKEN: Optional[str] = Field(default=None)
    MIXPANEL_SECRET: Optional[str] = Field(default=None)
    SENTRY_DSN: Optional[str] = Field(default=None)

    # Workflow settings
    WORKFLOW_API_ENDPOINT: Optional[str] = Field(default=None)
    WORKFLOW_SECRET_KEY: Optional[str] = Field(default=None)

    # Feature flags
    TESTING: bool = Field(default=False)
    WAITLIST_ENABLED: str = Field(default="false")
    QUEUE_NAME: str = Field(default="default")

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @validator("REDIS_URL", pre=True)
    def build_redis_url(cls, v, values):
        """Build Redis URL from components if not provided"""
        if v:
            return v

        password = values.get("REDIS_PASSWORD")
        host = values.get("REDIS_HOST", "localhost")
        port = values.get("REDIS_PORT", "6379")
        db = values.get("REDIS_DB", 0)

        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        return f"redis://{host}:{port}/{db}"

    # @validator("CELERY_BROKER_URL", pre=True)
    # def set_celery_broker_url(cls, v, values):
    #     """Set Celery broker URL from RabbitMQ URL if not provided"""
    #     if v:
    #         return v
    #     return values.get("RABBITMQ_BROKER_URL")

    @validator("CELERY_RESULT_BACKEND", pre=True)
    def set_celery_result_backend(cls, v, values):
        """Set Celery result backend from backend URL if not provided"""
        if v:
            return v
        return values.get("CELERY_BACKEND_URL")

    @validator("CLAUDE_API_KEY", pre=True)
    def set_claude_api_key(cls, v, values):
        """Use CLAUDE_KEY as fallback for CLAUDE_API_KEY"""
        if v:
            return v
        return values.get("CLAUDE_KEY")

    @validator("STORYBLOCKS_SECRET_KEY", pre=True)
    def set_storyblocks_secret_key(cls, v, values):
        """Use STORYBLOCKS_SCRECT_KEY as fallback (handles typo)"""
        if v:
            return v
        return values.get("STORYBLOCKS_SCRECT_KEY")

    @property
    def database_url(self) -> str:
        """Get the complete database URL"""
        return self.MONGO_URI

    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.ENV.lower() in ["dev", "development"]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.ENV.lower() in ["prod", "production"]

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode"""
        return self.ENV.lower() == "test" or self.TESTING

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields in environment


# Create settings instance with error handling
try:
    settings = Settings()
except ValidationError as e:
    print("Environment variable validation error:", e)
    raise

# Validate critical settings for production
if settings.is_production:
    critical_settings = [
        "SECRET_KEY",
        "MONGO_URI",
        "OPENAI_API_KEY",
    ]

    missing_settings = []
    for setting in critical_settings:
        if not getattr(settings, setting, None):
            missing_settings.append(setting)

    if missing_settings:
        raise ValueError(
            f"Missing critical settings for production: {', '.join(missing_settings)}"
        )

# Apply MoviePy settings if available
try:
    from moviepy.config import change_settings

    if settings.IMAGEMAGICK_BINARY:
        change_settings({"IMAGEMAGICK_BINARY": settings.IMAGEMAGICK_BINARY})
except ImportError:
    pass  # MoviePy not available

# Setup logger if available
try:
    from app.loggers.logger import setup_logger

    setup_logger()
except ImportError:
    pass  # Logger module not available
