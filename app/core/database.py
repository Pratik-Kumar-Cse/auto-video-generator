"""
Database connection and MongoDB setup
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database client and database instances
client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


async def init_db() -> None:
    """Initialize database connection"""
    global client, database

    try:
        # Create MongoDB client
        client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,  # 10 second timeout
            socketTimeoutMS=10000,  # 10 second timeout
            maxPoolSize=100,  # Maximum number of connections
            minPoolSize=10,  # Minimum number of connections
            maxIdleTimeMS=30000,  # Close connections after 30 seconds of inactivity
            retryWrites=True,
            retryReads=True,
        )

        # Get database
        database = client[settings.DATABASE_NAME]

        # Test connection
        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB database: {settings.DATABASE_NAME}")

        # Create indexes
        await create_indexes()

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


async def close_db() -> None:
    """Close database connection"""
    global client

    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if database is None:
        raise RuntimeError("Database not initialized")
    return database


async def create_indexes() -> None:
    """Create database indexes for optimal performance"""
    if database is None:
        return

    try:
        # Users collection indexes
        await database.users.create_index("email", unique=True)
        await database.users.create_index("created_at")
        await database.users.create_index([("email", 1), ("is_active", 1)])

        # Videos collection indexes
        await database.videos.create_index([("user_id", 1), ("created_at", -1)])
        await database.videos.create_index("status")
        await database.videos.create_index("task_id")
        await database.videos.create_index([("user_id", 1), ("status", 1)])
        await database.videos.create_index([("is_deleted", 1), ("created_at", -1)])
        await database.videos.create_index("view_type")

        # Scripts collection indexes
        await database.scripts.create_index([("user_id", 1), ("created_at", -1)])
        await database.scripts.create_index("script_type")
        await database.scripts.create_index([("user_id", 1), ("script_type", 1)])

        # Templates collection indexes
        await database.templates.create_index("template_type")
        await database.templates.create_index("is_active")
        await database.templates.create_index([("template_type", 1), ("is_active", 1)])

        # Avatars collection indexes
        await database.avatars.create_index([("user_id", 1), ("created_at", -1)])
        await database.avatars.create_index("provider")
        await database.avatars.create_index("is_active")

        # Voices collection indexes
        await database.voices.create_index("provider")
        await database.voices.create_index("language")
        await database.voices.create_index("gender")
        await database.voices.create_index([("provider", 1), ("language", 1)])

        # Subscriptions collection indexes
        await database.subscriptions.create_index("user_id", unique=True)
        await database.subscriptions.create_index("status")
        await database.subscriptions.create_index("expires_at")
        await database.subscriptions.create_index([("status", 1), ("expires_at", 1)])

        # Media collection indexes
        await database.media.create_index([("user_id", 1), ("created_at", -1)])
        await database.media.create_index("media_type")
        await database.media.create_index("provider")
        await database.media.create_index([("media_type", 1), ("provider", 1)])

        # Workflows collection indexes
        await database.workflows.create_index([("user_id", 1), ("created_at", -1)])
        await database.workflows.create_index("status")
        await database.workflows.create_index("workflow_type")

        # Analytics collection indexes
        await database.analytics.create_index([("user_id", 1), ("timestamp", -1)])
        await database.analytics.create_index("event_type")
        await database.analytics.create_index("timestamp")

        # Notifications collection indexes
        await database.notifications.create_index([("user_id", 1), ("created_at", -1)])
        await database.notifications.create_index("is_read")
        await database.notifications.create_index("notification_type")

        # Brands collection indexes
        await database.brands.create_index([("user_id", 1), ("created_at", -1)])
        await database.brands.create_index("is_active")

        # Upload sessions collection indexes
        await database.upload_sessions.create_index("session_id", unique=True)
        await database.upload_sessions.create_index("expires_at")
        await database.upload_sessions.create_index(
            [("user_id", 1), ("created_at", -1)]
        )

        logger.info("Database indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        # Don't raise here as indexes are not critical for startup


# Database health check
async def check_database_health() -> bool:
    """Check if database is healthy"""
    try:
        if not client:
            return False

        # Ping the database
        await client.admin.command("ping")
        return True

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Collection helpers
class Collections:
    """Database collection names"""

    USERS = "users"
    VIDEOS = "videos"
    SCRIPTS = "scripts"
    TEMPLATES = "templates"
    AVATARS = "avatars"
    VOICES = "voices"
    SUBSCRIPTIONS = "subscriptions"
    MEDIA = "media"
    WORKFLOWS = "workflows"
    ANALYTICS = "analytics"
    NOTIFICATIONS = "notifications"
    BRANDS = "brands"
    UPLOAD_SESSIONS = "upload_sessions"
    REFERRALS = "referrals"
    SCHEDULE_VIDEOS = "schedule_videos"


async def get_collection(collection_name: str):
    """Get a specific collection"""
    db = await get_database()
    return db[collection_name]
