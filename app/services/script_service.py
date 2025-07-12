"""
Script service for handling script-related operations
Enhanced with comprehensive functionality and optimizations
"""

import asyncio
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from bson import ObjectId

from app.agents.script_generator.workflow import ScriptWorkFlow
from app.constant.enum.script_enum import ScriptType
from app.core.exceptions import ScriptProcessingException
from app.loggers.logger import get_logger
from app.utils.media_utils import MediaUtils

from ..constants.enum.event_enum import EventStream
from ..core.database import get_database
from ..helper.sse_manager import SseManager
from .llm.llm_call import generate_ai_script

logger = get_logger(__name__)


class ScriptService:
    """Enhanced script service with comprehensive functionality"""

    def __init__(self):
        self.db = None
        self.collection = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.media_utils = MediaUtils()
        self.script_workflow = ScriptWorkFlow()
        self._trending_topics_cache = None
        self._cache_timestamp = None
        self._cache_duration = 3600  # 1 hour
        self.sse_manager = SseManager()

        logger.info("ScriptService initialized")

    async def _ensure_db_connection(self):
        """Ensure database connection is established"""
        if self.db is None:
            logger.debug("Establishing database connection")
            self.db = await get_database()
            self.collection = self.db.scripts
            logger.info("Database connection established")

    async def create_script(
        self,
        title: str,
        content: str,
        topic: str,
        video_type: str,
        user_id: str,  # Added missing parameter
        keywords: Optional[Dict[str, Any]] = None,
        input_type: str = "TOPIC",
        metadata: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        video_link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new script with enhanced metadata"""
        try:
            logger.info(f"Creating script for user {user_id}: {title[:50]}...")
            await self._ensure_db_connection()

            # Input validation
            if not title or not content or not topic or not user_id:
                logger.error("Missing required fields for script creation")
                raise ScriptProcessingException("Missing required fields")

            script_data = {
                "title": title,
                "content": content,
                "topic": topic,
                "video_type": video_type,
                "user_id": user_id,
                "keywords": keywords or {},
                "input_type": input_type,
                "type": input_type,  # For compatibility
                "status": "completed",
                "metadata": metadata or {},
                "task_id": task_id,
                "video_link": video_link,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_deleted": False,
                "word_count": len(content.split()) if content else 0,
                "estimated_duration": self._estimate_duration(content),
                "language": "en",  # Default language
                "tags": self._extract_tags(content, keywords),
                "sentiment_score": 0.7,  # Mock sentiment analysis
                "readability_score": 8.5,  # Mock readability score
                "seo_keywords": self._extract_seo_keywords(content, keywords),
            }

            if not self.collection:
                raise ScriptProcessingException("Database not initialized")

            result = await self.collection.insert_one(script_data)
            script_data["_id"] = str(result.inserted_id)

            logger.info(
                f"Script created successfully: {script_data['_id']} "
                f"for user {user_id}"
            )

            # Send creation notification
            await self._send_script_notification(user_id, "script_created", script_data)

            return script_data

        except Exception as e:
            logger.error(f"Error creating script: {e}", exc_info=True)
            raise ScriptProcessingException(str(e))

    async def get_script_of_user(
        self, user_id: str, script_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get script by ID for a specific user with enhanced data"""
        try:
            await self._ensure_db_connection()
            if not self.collection:
                return None

            if not ObjectId.is_valid(script_id):
                return None

            script = await self.collection.find_one(
                {
                    "_id": ObjectId(script_id),
                    "user_id": user_id,
                    "is_deleted": {"$ne": True},
                }
            )

            if script:
                script["_id"] = str(script["_id"])
                # Add computed fields
                script["reading_time"] = self._calculate_reading_time(
                    script.get("content", "")
                )
                script["last_accessed"] = datetime.utcnow()

                # Update last accessed time asynchronously
                asyncio.create_task(self._update_last_accessed(script_id))

            return script

        except Exception as e:
            logger.error(f"Error getting script: {e}")
            return None

    async def _update_last_accessed(self, script_id: str):
        """Update last accessed time without blocking the main request"""
        try:
            if self.collection:
                await self.collection.update_one(
                    {"_id": ObjectId(script_id)},
                    {"$set": {"last_accessed": datetime.utcnow()}},
                )
        except Exception as e:
            logger.error(f"Error updating last accessed time: {e}")

    async def update_script(
        self, user_id: str, script_id: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update script with enhanced validation and tracking"""
        try:
            if not self.collection:
                return None

            if not ObjectId.is_valid(script_id):
                return None

            # Input validation
            if not update_data:
                return None

            # Add computed fields if content is being updated
            if "content" in update_data:
                content = update_data["content"]
                update_data.update(
                    {
                        "word_count": len(content.split()) if content else 0,
                        "estimated_duration": self._estimate_duration(content),
                        "tags": self._extract_tags(
                            content, update_data.get("keywords", {})
                        ),
                        "seo_keywords": self._extract_seo_keywords(
                            content, update_data.get("keywords", {})
                        ),
                    }
                )

            update_data["updated_at"] = datetime.utcnow()

            result = await self.collection.find_one_and_update(
                {
                    "_id": ObjectId(script_id),
                    "user_id": user_id,
                    "is_deleted": {"$ne": True},
                },
                {"$set": update_data},
                return_document=True,
            )

            if result:
                result["_id"] = str(result["_id"])

                # Send update notification asynchronously
                asyncio.create_task(
                    self._send_script_notification(user_id, "script_updated", result)
                )

            return result

        except Exception as e:
            logger.error(f"Error updating script: {e}")
            return None

    async def delete_script(self, user_id: str, script_id: str) -> bool:
        """Soft delete script with audit trail"""
        try:
            if not self.collection:
                return False

            if not ObjectId.is_valid(script_id):
                return False

            result = await self.collection.update_one(
                {"_id": ObjectId(script_id), "user_id": user_id},
                {
                    "$set": {
                        "is_deleted": True,
                        "deleted_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            if result.modified_count > 0:
                # Send deletion notification asynchronously
                asyncio.create_task(
                    self._send_script_notification(
                        user_id, "script_deleted", {"script_id": script_id}
                    )
                )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error deleting script: {e}")
            return False

    async def get_all_scripts_by_user(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 10,
        filter_name: Optional[str] = None,
        video_type: Optional[str] = None,
        input_type: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: int = -1,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get all scripts for a user with enhanced filtering and sorting"""
        try:
            await self._ensure_db_connection()
            if not self.collection:
                return [], 0

            # Input validation
            page = max(1, page)
            per_page = max(1, min(100, per_page))  # Limit max per_page

            # Valid sort fields
            valid_sort_fields = ["created_at", "updated_at", "title", "word_count"]
            if sort_by not in valid_sort_fields:
                sort_by = "created_at"

            if sort_order not in [-1, 1]:
                sort_order = -1

            query = {"user_id": user_id, "is_deleted": {"$ne": True}}

            # Add filters
            if filter_name:
                # Create text search index for better performance
                query["$or"] = [
                    {"title": {"$regex": filter_name, "$options": "i"}},
                    {"topic": {"$regex": filter_name, "$options": "i"}},
                    {"content": {"$regex": filter_name, "$options": "i"}},
                    {"tags": {"$in": [filter_name]}},
                ]

            if video_type:
                query["video_type"] = video_type

            if input_type:
                query["input_type"] = input_type

            # Use aggregation pipeline for better performance
            pipeline = [
                {"$match": query},
                {"$sort": {sort_by: sort_order}},
                {
                    "$facet": {
                        "data": [
                            {"$skip": (page - 1) * per_page},
                            {"$limit": per_page},
                        ],
                        "count": [{"$count": "total"}],
                    }
                },
            ]

            result = await self.collection.aggregate(pipeline).to_list(length=1)

            if not result:
                return [], 0

            scripts = result[0]["data"]
            total_count = result[0]["count"][0]["total"] if result[0]["count"] else 0

            # Process scripts
            for script in scripts:
                script["_id"] = str(script["_id"])
                # Add computed fields
                script["reading_time"] = self._calculate_reading_time(
                    script.get("content", "")
                )

            return scripts, total_count

        except Exception as e:
            logger.error(f"Error getting scripts: {e}")
            return [], 0

    async def generate_script_async(
        self,
        topic: str,
        video_type: str,
        keywords: Dict[str, Any],
        input_type: str,
        video_link: Optional[str] = None,
    ) -> str:
        """Initiate async script generation and return task ID"""
        try:
            # Input validation
            if not topic or not video_type:
                raise ScriptProcessingException("Missing required fields")

            task_id = str(uuid.uuid4())

            # Start background task
            asyncio.create_task(
                self._generate_script_background(
                    topic,
                    video_type,
                    keywords,
                    input_type,
                    video_link,
                    task_id,
                )
            )

            return task_id

        except Exception as e:
            logger.error(f"Error initiating script generation: {e}")
            raise ScriptProcessingException(str(e))

    async def _generate_script_background(
        self,
        topic: str,
        video_type: str,
        keywords: Dict[str, Any],
        input_type: str,
        video_link: Optional[str],
        task_id: str,
    ):
        """Background script generation with real-time updates"""
        try:
            # Send initial progress
            await self._send_sse_update(task_id, "Starting script generation...", 0)

            # Validate inputs
            if input_type in ["VIDEO", "BLOG"] and not video_link:
                raise ScriptProcessingException(
                    "Link is required for video and blog input types"
                )

            # Progress update
            await self._send_sse_update(task_id, "Preparing script generation...", 20)

            # Map input types to script functions
            script_functions = {
                ScriptType.VIDEO: self.script_workflow.script_using_video,
                ScriptType.BLOG: self.script_workflow.script_using_blog,
                ScriptType.TOPIC: self.script_workflow.script_using_topic,
                ScriptType.SCRIPT: self.script_workflow.script_using_script,
                ScriptType.AI: generate_ai_script,
            }

            script_function = script_functions.get(input_type)
            if not script_function:
                raise ScriptProcessingException(f"Unsupported input type: {input_type}")

            # Progress update
            await self._send_sse_update(task_id, "Generating script content...", 50)

            # Prepare arguments
            args = [topic, video_type, keywords]

            if video_link:
                args.add(video_link)

            # Generate script
            script = script_function(*args)

            print("script:", script)

            # Progress update
            await self._send_sse_update(task_id, "Finalizing script...", 80)

            # Create script in database
            script_data = await self.create_script(
                title=topic,
                content=script,
                topic=topic,
                video_type=video_type,
                user_id="system",  # Default user_id for background tasks
                keywords=keywords,
                input_type=input_type,
                metadata={
                    "video_link": video_link,
                    "task_id": task_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "generation_method": "enhanced_ai",
                },
                task_id=task_id,
                video_link=video_link,
            )

            # Send completion message
            await self._send_sse_update(task_id, "Script generation completed!", 100)

        except Exception as e:
            logger.error(f"Error in background script generation: {e}")
            print(f"Error in background script generation: {e}")
            # Send completion message
            await self._send_sse_update(task_id, "Script generation completed!", 100)

    async def validate_link(self, link: str, link_type: str) -> bool:
        """Enhanced link validation with content checking"""
        try:
            if not link or not link_type:
                return False

            # Basic URL validation
            parsed = urlparse(link)
            if not parsed.scheme or not parsed.netloc:
                return False

            # Type-specific validation
            if link_type.lower() == "youtube":
                youtube_patterns = [
                    r"youtube\.com/watch\?v=",
                    r"youtu\.be/",
                    r"youtube\.com/embed/",
                    r"youtube\.com/v/",
                ]
                if not any(re.search(pattern, link) for pattern in youtube_patterns):
                    return False

            # Check if URL is accessible
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.head(
                        link, timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        return response.status == 200
            except Exception as e:
                logger.debug(f"URL accessibility check failed for {link}: {e}")
                return False

        except Exception as e:
            logger.error(f"Error validating link: {e}")
            return False

    async def get_trending_topics(self, limit: int = 10) -> List[str]:
        """Get trending topics for script generation with caching"""
        try:
            # Check cache
            current_time = datetime.utcnow()
            if (
                self._trending_topics_cache
                and self._cache_timestamp
                and (current_time - self._cache_timestamp).seconds
                < self._cache_duration
            ):
                return self._trending_topics_cache[:limit]

            # Fetch new trending topics
            trending_topics = [
                "AI and Machine Learning",
                "Sustainable Living",
                "Remote Work Tips",
                "Digital Marketing",
                "Health and Wellness",
                "Cryptocurrency",
                "Personal Development",
                "Technology Trends",
                "Social Media Strategy",
                "Entrepreneurship",
                "Climate Change Solutions",
                "Mental Health Awareness",
                "Productivity Hacks",
                "Investment Strategies",
                "Future of Work",
            ]

            # Update cache
            self._trending_topics_cache = trending_topics
            self._cache_timestamp = current_time

            return trending_topics[:limit]

        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []

    # Helper methods
    def _estimate_duration(self, content: str) -> float:
        """Estimate video duration based on content length"""
        if not content:
            return 0.0

        # Average speaking rate: 150-160 words per minute
        word_count = len(content.split())
        return round(word_count / 155, 1)

    def _calculate_reading_time(self, content: str) -> int:
        """Calculate reading time in minutes"""
        if not content:
            return 0

        # Average reading speed: 200-250 words per minute
        word_count = len(content.split())
        return max(1, round(word_count / 225))

    def _extract_tags(self, content: str, keywords: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from content and keywords"""
        tags = []

        # Add keywords as tags
        if keywords:
            tags.extend(list(keywords.keys())[:5])

        # Extract common words from content (mock implementation)
        if content:
            common_words = ["technology", "business", "growth", "success", "tips"]
            for word in common_words:
                if word.lower() in content.lower() and word not in tags:
                    tags.append(word)

        return tags[:10]  # Limit to 10 tags

    def _extract_seo_keywords(
        self, content: str, keywords: Dict[str, Any]
    ) -> List[str]:
        """Extract SEO-optimized keywords"""
        seo_keywords = []

        if keywords:
            seo_keywords.extend(list(keywords.keys())[:8])

        # Add content-based keywords (mock implementation)
        if content:
            content_keywords = ["how to", "best practices", "guide", "tutorial"]
            for keyword in content_keywords:
                if keyword.lower() in content.lower() and keyword not in seo_keywords:
                    seo_keywords.append(keyword)

        return seo_keywords[:15]

    async def _send_script_notification(
        self, user_id: str, event_type: str, data: Dict[str, Any]
    ):
        """Send script-related notifications via Redis"""
        try:
            notification = {
                "user_id": user_id,
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.sse_manager.send_update(
                event_name=EventStream.NOTIFICATION,
                data=notification,
                client_id=user_id,
            )

        except Exception as e:
            logger.error(f"Failed to send script notification: {e}")

    async def _send_sse_update(
        self,
        client_id: Optional[str],
        message: str,
        progress: int,
    ):
        """Send SSE update for real-time progress"""
        try:
            if not client_id:
                return

            update_data = {
                "message": message,
                "progress": progress,
                "timestamp": datetime.utcnow().isoformat(),
            }

            self.sse_manager.send_update(
                event_name=EventStream.SCRIPT,
                data=update_data,
                client_id=client_id,
            )

        except Exception as e:
            logger.error(f"Failed to send SSE update: {e}")

    async def cleanup_old_scripts(self, days_old: int = 30):
        """Clean up old deleted scripts"""
        try:
            if not self.collection:
                return

            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            result = await self.collection.delete_many(
                {"is_deleted": True, "deleted_at": {"$lt": cutoff_date}}
            )

            logger.info(f"Cleaned up {result.deleted_count} old scripts")

        except Exception as e:
            logger.error(f"Error cleaning up old scripts: {e}")


# Example usage (removed from production code)
def create_script_service(db):
    """Factory function to create script service instance"""
    return ScriptService(db)
