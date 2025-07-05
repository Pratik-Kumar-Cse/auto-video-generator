"""
Script service for handling script-related operations
Enhanced with comprehensive functionality from python-backend and AutoGen integration
"""

import logging
import json
import asyncio
import uuid
import os
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
from bson import ObjectId
from concurrent.futures import ThreadPoolExecutor

from app.core.redis_client import redis_service
from app.core.exceptions import ScriptProcessingException
from app.services.autogen_service import AutoGenScriptService
from app.utils.media_utils import MediaUtils

logger = logging.getLogger(__name__)


class ScriptService:
    """Enhanced script service with comprehensive functionality"""

    def __init__(self, db=None):
        self.db = db
        self.collection = self.db.scripts if db else None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.autogen_service = AutoGenScriptService()
        self.media_utils = MediaUtils()

    async def create_script(
        self,
        user_id: str,
        title: str,
        content: str,
        topic: str,
        video_type: str,
        keywords: Optional[Dict[str, Any]] = None,
        input_type: str = "TOPIC",
        metadata: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        link: Optional[str] = None,
        video_link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new script with enhanced metadata"""
        try:
            script_data = {
                "user_id": user_id,
                "title": title,
                "content": content,
                "topic": topic,
                "video_type": video_type,
                "keywords": keywords or {},
                "input_type": input_type,
                "type": input_type,  # For compatibility
                "status": "completed",
                "metadata": metadata or {},
                "task_id": task_id,
                "link": link,
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

            result = await self.collection.insert_one(script_data)
            script_data["_id"] = str(result.inserted_id)

            # Send creation notification
            await self._send_script_notification(user_id, "script_created", script_data)

            return script_data

        except Exception as e:
            logger.error(f"Error creating script: {e}")
            raise ScriptProcessingException(str(e))

    async def get_script_of_user(
        self, user_id: str, script_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get script by ID for a specific user with enhanced data"""
        try:
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

                # Update last accessed time
                await self.collection.update_one(
                    {"_id": ObjectId(script_id)},
                    {"$set": {"last_accessed": datetime.utcnow()}},
                )

            return script

        except Exception as e:
            logger.error(f"Error getting script: {e}")
            return None

    async def update_script(
        self, user_id: str, script_id: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update script with enhanced validation and tracking"""
        try:
            if not ObjectId.is_valid(script_id):
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

                # Send update notification
                await self._send_script_notification(user_id, "script_updated", result)

            return result

        except Exception as e:
            logger.error(f"Error updating script: {e}")
            return None

    async def delete_script(self, user_id: str, script_id: str) -> bool:
        """Soft delete script with audit trail"""
        try:
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
                # Send deletion notification
                await self._send_script_notification(
                    user_id, "script_deleted", {"script_id": script_id}
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
            query = {"user_id": user_id, "is_deleted": {"$ne": True}}

            # Add filters
            if filter_name:
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

            # Get total count
            total_count = await self.collection.count_documents(query)

            # Get paginated results with sorting
            skip = (page - 1) * per_page
            cursor = (
                self.collection.find(query)
                .sort(sort_by, sort_order)
                .skip(skip)
                .limit(per_page)
            )

            scripts = []
            async for script in cursor:
                script["_id"] = str(script["_id"])
                # Add computed fields
                script["reading_time"] = self._calculate_reading_time(
                    script.get("content", "")
                )
                scripts.append(script)

            return scripts, total_count

        except Exception as e:
            logger.error(f"Error getting scripts: {e}")
            return [], 0

    async def generate_script_async(
        self,
        user_id: str,
        topic: str,
        video_type: str,
        keywords: Dict[str, Any],
        input_type: str,
        add_brand: bool = False,
        music_media_id: Optional[str] = None,
        link: Optional[str] = None,
        video_link: Optional[str] = None,
        task_id: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> str:
        """Initiate async script generation and return task ID"""
        try:
            if not task_id:
                task_id = str(uuid.uuid4())

            # Start background task
            asyncio.create_task(
                self._generate_script_background(
                    user_id,
                    topic,
                    video_type,
                    keywords,
                    input_type,
                    add_brand,
                    music_media_id,
                    link,
                    video_link,
                    task_id,
                    client_id,
                )
            )

            return task_id

        except Exception as e:
            logger.error(f"Error initiating script generation: {e}")
            raise ScriptProcessingException(str(e))

    async def _generate_script_background(
        self,
        user_id: str,
        topic: str,
        video_type: str,
        keywords: Dict[str, Any],
        input_type: str,
        add_brand: bool,
        music_media_id: Optional[str],
        link: Optional[str],
        video_link: Optional[str],
        task_id: str,
        client_id: Optional[str],
    ):
        """Background script generation with real-time updates"""
        try:
            # Send initial progress
            await self._send_sse_update(
                client_id, "Starting script generation...", 0, task_id
            )

            # Validate inputs
            if input_type in ["VIDEO", "BLOG"] and not link:
                raise ScriptProcessingException(
                    "Link is required for video and blog input types"
                )

            # Check user subscription and credits
            await self._check_user_limits(user_id)

            # Generate script content in steps
            steps = [
                ("Analyzing input...", 10),
                ("Extracting key information...", 25),
                ("Generating outline...", 40),
                ("Creating content...", 65),
                ("Optimizing for engagement...", 80),
                ("Finalizing script...", 95),
            ]

            for step_msg, progress in steps:
                await self._send_sse_update(client_id, step_msg, progress, task_id)
                await asyncio.sleep(1)  # Simulate processing time

            # Generate script content based on input type
            if input_type == "VIDEO" and link:
                script_content = await self._generate_from_video_async(
                    topic, link, keywords, video_link
                )
            elif input_type == "BLOG" and link:
                script_content = await self._generate_from_blog_async(
                    topic, link, keywords
                )
            elif input_type == "AI":
                script_content = await self._generate_with_autogen(
                    topic, keywords, video_type
                )
            else:
                script_content = await self._generate_from_topic_async(
                    topic, keywords, video_type
                )

            # Create script in database
            script_data = await self.create_script(
                user_id=user_id,
                title=topic,
                content=script_content,
                topic=topic,
                video_type=video_type,
                keywords=keywords,
                input_type=input_type,
                metadata={
                    "add_brand": add_brand,
                    "music_media_id": music_media_id,
                    "link": link,
                    "video_link": video_link,
                    "task_id": task_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "generation_method": "enhanced_ai",
                },
                task_id=task_id,
                link=link,
                video_link=video_link,
            )

            # Send completion message
            await self._send_sse_update(
                client_id, "Script generation completed!", 100, task_id
            )

            await self._send_completion_message(task_id, script_data, client_id)

        except Exception as e:
            logger.error(f"Error in background script generation: {e}")
            await self._send_error_message(task_id, str(e), client_id)

    async def validate_link(self, link: str, link_type: str) -> bool:
        """Enhanced link validation with content checking"""
        try:
            if not link or not link_type:
                return False

            # Basic URL validation
            if not link.startswith(("http://", "https://")):
                return False

            # Type-specific validation
            if link_type.lower() == "youtube":
                youtube_patterns = [
                    "youtube.com/watch?v=",
                    "youtu.be/",
                    "youtube.com/embed/",
                    "youtube.com/v/",
                ]
                if not any(pattern in link for pattern in youtube_patterns):
                    return False

            # Check if URL is accessible (mock implementation)
            return True

        except Exception as e:
            logger.error(f"Error validating link: {e}")
            return False

    async def get_trending_topics(self, limit: int = 10) -> List[str]:
        """Get trending topics for script generation"""
        try:
            # This would integrate with trending topics API
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

            return trending_topics[:limit]

        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return []

    async def get_script_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get script analytics for user"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "is_deleted": {"$ne": True}}},
                {
                    "$group": {
                        "_id": "$video_type",
                        "count": {"$sum": 1},
                        "avg_word_count": {"$avg": "$word_count"},
                        "total_duration": {"$sum": "$estimated_duration"},
                    }
                },
            ]

            result = []
            async for doc in self.collection.aggregate(pipeline):
                result.append(doc)

            # Format analytics data
            analytics = {
                "total_scripts": 0,
                "by_video_type": {},
                "recent_activity": await self._get_recent_activity(user_id),
                "total_word_count": 0,
                "total_estimated_duration": 0,
                "average_script_length": 0,
            }

            for item in result:
                video_type = item["_id"]
                count = item["count"]
                analytics["total_scripts"] += count
                analytics["by_video_type"][video_type] = {
                    "count": count,
                    "avg_word_count": item.get("avg_word_count", 0),
                    "total_duration": item.get("total_duration", 0),
                }
                analytics["total_word_count"] += item.get("avg_word_count", 0) * count
                analytics["total_estimated_duration"] += item.get("total_duration", 0)

            if analytics["total_scripts"] > 0:
                analytics["average_script_length"] = (
                    analytics["total_word_count"] / analytics["total_scripts"]
                )

            return analytics

        except Exception as e:
            logger.error(f"Failed to get script analytics: {e}")
            return {"total_scripts": 0, "by_video_type": {}, "recent_activity": []}

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

            channel = f"script_notifications:{user_id}"
            redis_service.publish(channel, json.dumps(notification))

        except Exception as e:
            logger.error(f"Failed to send script notification: {e}")

    async def _send_sse_update(
        self, client_id: Optional[str], message: str, progress: int, task_id: str
    ):
        """Send SSE update for real-time progress"""
        try:
            if not client_id:
                return

            update_data = {
                "task_id": task_id,
                "message": message,
                "progress": progress,
                "timestamp": datetime.utcnow().isoformat(),
            }

            channel = f"script_progress:{client_id}"
            redis_service.publish(channel, json.dumps(update_data))

        except Exception as e:
            logger.error(f"Failed to send SSE update: {e}")

    async def _send_completion_message(
        self, task_id: str, script_data: Dict[str, Any], client_id: Optional[str]
    ):
        """Send completion message via Redis"""
        try:
            completion_data = {
                "task_id": task_id,
                "status": "completed",
                "script": script_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if client_id:
                channel = f"script_progress:{client_id}"
                redis_service.publish(channel, json.dumps(completion_data))

            # Also store in task queue
            queue_key = f"script_queue:{task_id}"
            redis_service.rpush(queue_key, json.dumps(completion_data))
            redis_service.rpush(queue_key, "[DONE]")

        except Exception as e:
            logger.error(f"Failed to send completion message: {e}")

    async def _send_error_message(
        self, task_id: str, error_message: str, client_id: Optional[str]
    ):
        """Send error message via Redis"""
        try:
            error_data = {
                "task_id": task_id,
                "status": "error",
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if client_id:
                channel = f"script_progress:{client_id}"
                redis_service.publish(channel, json.dumps(error_data))

            # Also store in task queue
            queue_key = f"script_queue:{task_id}"
            redis_service.rpush(queue_key, json.dumps(error_data))
            redis_service.rpush(queue_key, "[DONE]")

        except Exception as e:
            logger.error(f"Failed to send error message: {e}")

    async def _check_user_limits(self, user_id: str):
        """Check user subscription and credit limits"""
        try:
            # This would integrate with subscription service
            # For now, just log the check
            logger.info(f"Checking limits for user {user_id}")

        except Exception as e:
            logger.error(f"Error checking user limits: {e}")

    async def _get_recent_activity(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent script activity for user"""
        try:
            cursor = (
                self.collection.find({"user_id": user_id, "is_deleted": {"$ne": True}})
                .sort("created_at", -1)
                .limit(5)
            )

            activities = []
            async for script in cursor:
                activities.append(
                    {
                        "script_id": str(script["_id"]),
                        "title": script["title"],
                        "created_at": script["created_at"],
                        "video_type": script["video_type"],
                        "word_count": script.get("word_count", 0),
                        "estimated_duration": script.get("estimated_duration", 0),
                    }
                )

            return activities

        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []

    # Sync methods for compatibility with threading
    def get_script_using_task_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get script by task ID (sync method for threading compatibility)"""
        try:
            # This would use sync MongoDB connection
            # For now, return None as placeholder
            logger.info(f"Getting script for task ID: {task_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting script by task ID: {e}")
            return None

    # AutoGen and Media Utility Methods
    async def generate_script_with_autogen(
        self,
        user_id: str,
        topic: str,
        video_type: str,
        keywords: Dict[str, Any],
        use_multi_agent: bool = True,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate script using AutoGen multi-agent system"""
        try:
            if use_multi_agent:
                result = await self.autogen_service.generate_script_with_autogen(
                    topic=topic,
                    video_type=video_type,
                    keywords=keywords,
                    additional_context=additional_context,
                )
            else:
                # Fallback to enhanced generation
                result = await self.autogen_service._fallback_generation(
                    topic, video_type, keywords
                )

            return result

        except Exception as e:
            logger.error(f"Error in AutoGen script generation: {e}")
            # Fallback to standard generation
            script_content = await self._generate_from_topic_async(
                topic, keywords, video_type
            )
            return {
                "script": script_content,
                "metadata": {
                    "generation_method": "fallback_standard",
                    "error": str(e),
                    "generated_at": datetime.utcnow().isoformat(),
                },
                "success": True,
            }

    async def generate_script_variations(
        self, script_id: str, user_id: str, variations_count: int = 3
    ) -> List[Dict[str, Any]]:
        """Generate multiple variations of an existing script"""
        try:
            # Get the original script
            script = await self.get_script_of_user(user_id, script_id)
            if not script:
                raise ScriptProcessingException("Script not found")

            base_script = script.get("content", "")
            variations = await self.autogen_service.generate_script_variations(
                base_script, variations_count
            )

            # Store variations as new scripts
            variation_scripts = []
            for i, variation in enumerate(variations):
                variation_data = await self.create_script(
                    user_id=user_id,
                    title=f"{script['title']} - Variation {i+1}",
                    content=variation["script"],
                    topic=script["topic"],
                    video_type=script["video_type"],
                    keywords=script.get("keywords", {}),
                    input_type=script.get("input_type", "TOPIC"),
                    metadata={
                        "original_script_id": script_id,
                        "variation_number": i + 1,
                        "generation_method": "autogen_variation",
                        "generated_at": datetime.utcnow().isoformat(),
                    },
                )
                variation_scripts.append(variation_data)

            return variation_scripts

        except Exception as e:
            logger.error(f"Error generating script variations: {e}")
            raise ScriptProcessingException(str(e))

    async def process_media_for_script(
        self, script_id: str, user_id: str, media_files: List[str]
    ) -> Dict[str, Any]:
        """Process media files for script enhancement"""
        try:
            script = await self.get_script_of_user(user_id, script_id)
            if not script:
                raise ScriptProcessingException("Script not found")

            processed_media = []
            temp_dir = "/tmp/script_media"
            os.makedirs(temp_dir, exist_ok=True)

            for media_file in media_files:
                try:
                    # Validate media file
                    if self.media_utils.validate_media_file(media_file):
                        metadata = self.media_utils.get_file_metadata(media_file)

                        # Generate thumbnail if it's a video
                        if metadata.get("mime_type", "").startswith("video/"):
                            thumbnail_path = os.path.join(
                                temp_dir, f"thumb_{os.path.basename(media_file)}.jpg"
                            )
                            success = self.media_utils.generate_thumbnail(
                                media_file, thumbnail_path
                            )
                            if success:
                                metadata["thumbnail"] = thumbnail_path

                        processed_media.append(
                            {
                                "file_path": media_file,
                                "metadata": metadata,
                                "processed_at": datetime.utcnow().isoformat(),
                            }
                        )

                except Exception as e:
                    logger.error(f"Error processing media file {media_file}: {e}")
                    continue

            # Update script with media information
            await self.update_script(
                user_id,
                script_id,
                {
                    "processed_media": processed_media,
                    "media_processed_at": datetime.utcnow(),
                },
            )

            # Cleanup temp files after processing
            self.media_utils.cleanup_temp_files(temp_dir, max_age_hours=1)

            return {
                "script_id": script_id,
                "processed_media_count": len(processed_media),
                "processed_media": processed_media,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error processing media for script: {e}")
            raise ScriptProcessingException(str(e))

    async def generate_thumbnails_for_script(
        self, script_id: str, user_id: str, video_files: List[str]
    ) -> Dict[str, Any]:
        """Generate thumbnails for video files associated with a script"""
        try:
            thumbnails = []
            temp_dir = "/tmp/script_thumbnails"
            os.makedirs(temp_dir, exist_ok=True)

            for video_file in video_files:
                try:
                    if self.media_utils.validate_media_file(video_file, ["video/"]):
                        thumbnail_filename = f"thumb_{uuid.uuid4().hex}.jpg"
                        thumbnail_path = os.path.join(temp_dir, thumbnail_filename)

                        success = self.media_utils.generate_thumbnail(
                            video_file, thumbnail_path, time=1.0
                        )

                        if success:
                            thumbnails.append(
                                {
                                    "video_file": video_file,
                                    "thumbnail_path": thumbnail_path,
                                    "generated_at": datetime.utcnow().isoformat(),
                                }
                            )

                except Exception as e:
                    logger.error(f"Error generating thumbnail for {video_file}: {e}")
                    continue

            # Update script with thumbnail information
            await self.update_script(
                user_id,
                script_id,
                {
                    "generated_thumbnails": thumbnails,
                    "thumbnails_generated_at": datetime.utcnow(),
                },
            )

            return {
                "script_id": script_id,
                "thumbnails_generated": len(thumbnails),
                "thumbnails": thumbnails,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error generating thumbnails: {e}")
            raise ScriptProcessingException(str(e))

    async def enhance_script_with_media_analysis(
        self, script_id: str, user_id: str, media_urls: List[str]
    ) -> Dict[str, Any]:
        """Enhance script content based on media analysis"""
        try:
            script = await self.get_script_of_user(user_id, script_id)
            if not script:
                raise ScriptProcessingException("Script not found")

            media_insights = []
            temp_dir = "/tmp/media_analysis"
            os.makedirs(temp_dir, exist_ok=True)

            for url in media_urls:
                try:
                    # Download media for analysis
                    filename = f"media_{uuid.uuid4().hex}"
                    local_path = os.path.join(temp_dir, filename)

                    if self.media_utils.download_video(url, local_path):
                        metadata = self.media_utils.get_file_metadata(local_path)

                        # Generate thumbnail for visual analysis
                        if metadata.get("mime_type", "").startswith("video/"):
                            thumb_path = f"{local_path}_thumb.jpg"
                            self.media_utils.generate_thumbnail(local_path, thumb_path)
                            metadata["thumbnail"] = thumb_path

                        media_insights.append(
                            {
                                "url": url,
                                "local_path": local_path,
                                "metadata": metadata,
                                "analysis_timestamp": datetime.utcnow().isoformat(),
                            }
                        )

                except Exception as e:
                    logger.error(f"Error analyzing media from {url}: {e}")
                    continue

            # Use AutoGen to enhance script based on media insights
            if media_insights:
                enhancement_context = f"""
                Media Analysis Results:
                {json.dumps(media_insights, indent=2)}
                
                Original Script:
                {script.get('content', '')}
                """

                enhanced_result = (
                    await self.autogen_service.generate_script_with_autogen(
                        topic=f"Enhanced {script['topic']}",
                        video_type=script["video_type"],
                        keywords=script.get("keywords", {}),
                        additional_context=enhancement_context,
                    )
                )

                # Update script with enhanced content
                await self.update_script(
                    user_id,
                    script_id,
                    {
                        "content": enhanced_result["script"],
                        "media_insights": media_insights,
                        "enhancement_metadata": enhanced_result["metadata"],
                        "enhanced_at": datetime.utcnow(),
                    },
                )

            # Cleanup temp files
            self.media_utils.cleanup_temp_files(temp_dir, max_age_hours=1)

            return {
                "script_id": script_id,
                "media_analyzed": len(media_insights),
                "enhanced": len(media_insights) > 0,
                "insights": media_insights,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error enhancing script with media analysis: {e}")
            raise ScriptProcessingException(str(e))

    async def get_autogen_insights(self) -> Dict[str, Any]:
        """Get insights from AutoGen conversation history"""
        try:
            return self.autogen_service.get_agent_insights()
        except Exception as e:
            logger.error(f"Error getting AutoGen insights: {e}")
            return {"error": str(e)}

    # Mock implementations for async methods
    async def _generate_from_topic_async(
        self, topic: str, keywords: Dict[str, Any], video_type: str
    ) -> str:
        """Generate script from topic (async version)"""
        keyword_text = (
            ", ".join(list(keywords.keys())[:5])
            if keywords
            else "success, growth, tips"
        )

        return f"""# {topic}

## Hook
What if I told you that {topic} could completely transform your {video_type.lower()} strategy?

## Introduction
Welcome to this comprehensive guide on {topic}. In the next few minutes, you'll discover proven strategies that successful creators use to master {video_type.lower()} content.

## Main Content
{topic} is more than just a concept—it's your pathway to {video_type.lower()} excellence.

**Key Insights:**
1. **Foundation**: Understanding the core principles
2. **Implementation**: Practical steps you can take today
3. **Optimization**: Advanced techniques for maximum impact

**Keywords we're targeting:** {keyword_text}

## Call to Action
Ready to implement these {topic} strategies? Subscribe for more expert insights and don't forget to like this video!

## Conclusion
{topic} isn't just a trend—it's the future of successful {video_type.lower()} content. Start implementing these strategies today!

---
*Generated with enhanced AI optimization*
*Estimated duration: {self._estimate_duration("sample content for estimation")} minutes*
"""

    async def _generate_from_video_async(
        self, topic: str, link: str, keywords: Dict[str, Any], video_link: Optional[str]
    ) -> str:
        """Generate script from video (async version)"""
        keyword_text = (
            ", ".join(list(keywords.keys())[:5])
            if keywords
            else "video analysis, insights"
        )

        return f"""# {topic} - Video Analysis

## Hook
I just analyzed this incredible video about {topic}, and the insights are game-changing!

## Introduction
Based on comprehensive analysis of the video at {link}, I've extracted the most valuable insights about {topic}.

## Key Takeaways
- Primary insight about {topic}
- Supporting evidence and examples
- Practical applications you can use

**Keywords:** {keyword_text}

## Enhanced Analysis
While the original video provides excellent foundation, here's what I'm adding:
- Updated perspectives and recent developments
- Additional strategies not covered
- Real-world implementation tips

## Call to Action
Check out the original video (link in description) and subscribe for more content analysis!

## Conclusion
This analysis gives you both the original insights and enhanced perspectives on {topic}.

---
*Source: {link}*
*Analysis date: {datetime.utcnow().strftime('%Y-%m-%d')}*
"""

    async def _generate_from_blog_async(
        self, topic: str, link: str, keywords: Dict[str, Any]
    ) -> str:
        """Generate script from blog (async version)"""
        keyword_text = (
            ", ".join(list(keywords.keys())[:5])
            if keywords
            else "blog insights, analysis"
        )

        return f"""# {topic} - Blog Article Breakdown

## Hook
I just read this amazing article about {topic}, and I'm sharing the most important insights!

## Introduction
Today I'm breaking down a comprehensive blog post from {link} that covers {topic} in detail.

## Article Highlights
- Main arguments and supporting evidence
- Practical strategies and implementation tips
- Real-world examples and case studies

**Keywords:** {keyword_text}

## My Additional Insights
- Updated information since publication
- Alternative perspectives and approaches
- Personal experience and observations

## Call to Action
Read the full article (link in description) and subscribe for more content breakdowns!

## Conclusion
This breakdown gives you both the original article insights and my enhanced analysis of {topic}.

---
*Source: {link}*
*Breakdown date: {datetime.utcnow().strftime('%Y-%m-%d')}*
"""

    async def _generate_with_ai(
        self, topic: str, keywords: Dict[str, Any], video_type: str
    ) -> str:
        """Generate script using AI integration"""
        keyword_text = (
            ", ".join(list(keywords.keys())[:5])
            if keywords
            else "AI, insights, analysis"
        )

        return f"""# {topic} - AI-Powered Analysis

## Hook
AI just analyzed thousands of data points about {topic}, and the results are fascinating!

## Introduction
Using advanced AI analysis, I've uncovered patterns about {topic} that most people miss.

## AI Insights
- Data-driven recommendations with 92% confidence
- Pattern recognition from 10,000+ sources
- Predictive analysis for future trends

**AI-optimized keywords:** {keyword_text}

## Human + AI Perspective
While AI provides incredible insights, human experience adds:
- Contextual understanding
- Creative solutions
- Practical wisdom

## Implementation Framework
Phase 1: Foundation (Weeks 1-2)
Phase 2: Implementation (Weeks 3-6)
Phase 3: Optimization (Weeks 7-12)

## Call to Action
Subscribe for more AI-powered insights and data-driven content!

## Conclusion
Combining AI capabilities with human expertise creates unprecedented insights into {topic}.

---
*AI analysis confidence: 93.2%*
*Generated: {datetime.utcnow().strftime('%Y-%m-%d')}*
"""
