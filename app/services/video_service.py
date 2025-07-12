"""
Video service for handling video-related operations
Enhanced with comprehensive functionality from python-backend
"""

import logging
import asyncio
import json
import os
import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.core.redis_client import redis_service
from app.core.exceptions import (
    VideoNotFoundException,
    VideoProcessingException,
    SubscriptionInactiveException,
    InsufficientCreditsException,
    BadRequestException,
)
from app.models.video import VideoStatus, VideoViewType

logger = logging.getLogger(__name__)


class VideoService:
    """Service class for video operations"""

    def __init__(self, db=None):
        self.db = db
        self.collection = self.db.videos if db else None

    async def create_video(
        self,
        user_id: str,
        script_id: str,
        voice_id: Optional[str] = None,
        avatar_id: Optional[str] = None,
        template_id: Optional[str] = None,
        view_type: str = "PORTRAIT",
        caption: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new video record"""
        try:
            video_doc = {
                "user_id": user_id,
                "script_id": script_id,
                "voice_id": voice_id,
                "avatar_id": avatar_id,
                "template_id": template_id,
                "view_type": view_type,
                "caption": caption,
                "status": VideoStatus.PENDING.value,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "link": None,
                "title": None,
                "avatar_video_ids": [],
                "avatar_video_urls": [],
                "status_message": None,
                "metadata": {},
                "link_1080p": None,
                "thumbnail_link": None,
                "is_community_video": False,
                "task_id": None,
                "is_deleted": False,
            }

            result = await self.collection.insert_one(video_doc)
            video_doc["_id"] = result.inserted_id
            return video_doc

        except Exception as e:
            logger.error(f"Failed to create video: {e}")
            raise VideoProcessingException(f"Failed to create video: {str(e)}")

    async def get_video_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video by ID"""
        try:
            if not ObjectId.is_valid(video_id):
                return None

            video = await self.collection.find_one(
                {"_id": ObjectId(video_id), "is_deleted": {"$ne": True}}
            )

            if video:
                video["_id"] = str(video["_id"])

            return video

        except Exception as e:
            logger.error(f"Failed to get video: {e}")
            return None

    async def get_video_by_user_id(
        self, user_id: str, video_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get video by user ID and video ID"""
        try:
            if not ObjectId.is_valid(video_id):
                return None

            video = await self.collection.find_one(
                {
                    "_id": ObjectId(video_id),
                    "user_id": user_id,
                    "is_deleted": {"$ne": True},
                }
            )

            if video:
                video["_id"] = str(video["_id"])

            return video

        except Exception as e:
            logger.error(f"Failed to get video by user: {e}")
            return None

    async def get_video_details(
        self, video_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed video information with script data"""
        try:
            if not ObjectId.is_valid(video_id):
                return None

            pipeline = [
                {
                    "$match": {
                        "_id": ObjectId(video_id),
                        "user_id": user_id,
                        "is_deleted": {"$ne": True},
                    }
                },
                {
                    "$lookup": {
                        "from": "scripts",
                        "localField": "script_id",
                        "foreignField": "_id",
                        "as": "script_data",
                    }
                },
                {
                    "$unwind": {
                        "path": "$script_data",
                        "preserveNullAndEmptyArrays": True,
                    }
                },
            ]

            cursor = self.collection.aggregate(pipeline)
            video = await cursor.to_list(length=1)

            if video:
                video = video[0]
                video["_id"] = str(video["_id"])
                if "script_data" in video and video["script_data"]:
                    video["script_data"]["_id"] = str(video["script_data"]["_id"])
                return video

            return None

        except Exception as e:
            logger.error(f"Failed to get video details: {e}")
            return None

    async def find_videos_by_user_id(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 10,
        status: Optional[str] = None,
        view_type: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get videos by user ID with pagination and filtering"""
        try:
            query = {"user_id": user_id, "is_deleted": {"$ne": True}}

            if status:
                query["status"] = status
            if view_type:
                query["view_type"] = view_type
            if title:
                query["title"] = {"$regex": title, "$options": "i"}

            # Count total documents
            total_count = await self.collection.count_documents(query)

            # Calculate skip value
            skip = (page - 1) * per_page
            total_pages = -(-total_count // per_page)  # Ceiling division

            # Get videos with pagination
            cursor = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(per_page)
            )

            videos = []
            async for video in cursor:
                video["_id"] = str(video["_id"])
                videos.append(video)

            return {
                "videos": videos,
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
            }

        except Exception as e:
            logger.error(f"Failed to get user videos: {e}")
            raise VideoProcessingException(f"Failed to get user videos: {str(e)}")

    async def find_community_videos(
        self, page: int = 1, per_page: int = 10, view_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get community videos with pagination"""
        try:
            query = {
                "is_community_video": True,
                "status": VideoStatus.COMPLETED.value,
                "is_deleted": {"$ne": True},
            }

            if view_type:
                query["view_type"] = view_type

            # Count total documents
            total_count = await self.collection.count_documents(query)

            # Calculate skip value
            skip = (page - 1) * per_page
            total_pages = -(-total_count // per_page)  # Ceiling division

            # Get videos with pagination
            cursor = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(per_page)
            )

            videos = []
            async for video in cursor:
                video["_id"] = str(video["_id"])
                videos.append(video)

            return {
                "videos": videos,
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
            }

        except Exception as e:
            logger.error(f"Failed to get community videos: {e}")
            raise VideoProcessingException(f"Failed to get community videos: {str(e)}")

    async def update_video(
        self, video_id: str, update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update video by ID"""
        try:
            if not ObjectId.is_valid(video_id):
                return None

            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()

            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(video_id), "is_deleted": {"$ne": True}},
                {"$set": update_data},
                return_document=True,
            )

            if result:
                result["_id"] = str(result["_id"])

            return result

        except Exception as e:
            logger.error(f"Failed to update video: {e}")
            return None

    async def soft_delete_video(self, video_id: str) -> bool:
        """Soft delete video by ID"""
        try:
            if not ObjectId.is_valid(video_id):
                return False

            result = await self.collection.update_one(
                {"_id": ObjectId(video_id)},
                {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}},
            )

            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Failed to delete video: {e}")
            return False

    async def upload_video(
        self, user_id: str, video: Dict[str, Any], upload_domain: str
    ) -> Dict[str, Any]:
        """Upload video to external platform"""
        try:
            # This would integrate with external upload services
            # For now, return a mock response
            upload_result = {
                "id": f"uploaded_{video['_id']}_{upload_domain}",
                "platform": upload_domain,
                "url": f"https://{upload_domain}.com/video/{video['_id']}",
                "status": "uploaded",
            }

            # Update video with upload information
            await self.update_video(
                video["_id"], {"upload_info": {upload_domain: upload_result}}
            )

            return upload_result

        except Exception as e:
            logger.error(f"Failed to upload video: {e}")
            raise VideoProcessingException(f"Failed to upload video: {str(e)}")

    async def get_download_url(
        self, user_id: str, video: Dict[str, Any], quality: str = "720p"
    ) -> str:
        """Get download URL for video"""
        try:
            if quality == "1080p" and video.get("link_1080p"):
                return video["link_1080p"]
            elif video.get("link"):
                return video["link"]
            else:
                raise VideoProcessingException("Video download link not available")

        except Exception as e:
            logger.error(f"Failed to get download URL: {e}")
            raise VideoProcessingException(f"Failed to get download URL: {str(e)}")

    async def generate_youtube_metadata(self, video: Dict[str, Any]) -> Dict[str, Any]:
        """Generate YouTube metadata for video"""
        try:
            # This would integrate with AI service to generate metadata
            # For now, return a mock response
            metadata = {
                "title": video.get("title", "Generated Video"),
                "description": f"Video generated from script: {video.get('script_id')}",
                "tags": ["ai", "generated", "video"],
                "category_id": "22",  # People & Blogs
                "privacy_status": "public",
            }

            # Update video with generated metadata
            await self.update_video(video["_id"], {"metadata": metadata})

            return metadata

        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            raise VideoProcessingException(f"Failed to generate metadata: {str(e)}")

    async def generate_video_using_workflow(
        self, request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate video using workflow with script generation"""
        try:
            # This would integrate with the complete workflow
            # For now, return a mock response
            workflow_result = {
                "video_id": str(ObjectId()),
                "script_id": str(ObjectId()),
                "status": "initiated",
                "workflow_type": "complete",
            }

            return workflow_result

        except Exception as e:
            logger.error(f"Failed to generate workflow video: {e}")
            raise VideoProcessingException(
                f"Failed to generate workflow video: {str(e)}"
            )

    async def generate_video_using_workflow_with_video_id(
        self, video_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Generate video using workflow with existing video ID"""
        try:
            video = await self.get_video_by_user_id(user_id, video_id)
            if not video:
                raise VideoNotFoundException(video_id)

            # This would integrate with the complete workflow
            # For now, return a mock response
            workflow_result = {
                "video_id": video_id,
                "status": "initiated",
                "workflow_type": "existing_video",
            }

            return workflow_result

        except Exception as e:
            logger.error(f"Failed to generate workflow video by ID: {e}")
            raise VideoProcessingException(
                f"Failed to generate workflow video by ID: {str(e)}"
            )

    async def get_video_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get video analytics for user"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "is_deleted": {"$ne": True}}},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            ]

            result = []
            async for doc in self.collection.aggregate(pipeline):
                result.append(doc)

            # Format analytics data
            analytics = {
                "total_videos": 0,
                "completed_videos": 0,
                "processing_videos": 0,
                "failed_videos": 0,
                "pending_videos": 0,
            }

            for item in result:
                status = item["_id"]
                count = item["count"]
                analytics["total_videos"] += count

                if status == VideoStatus.COMPLETED.value:
                    analytics["completed_videos"] = count
                elif status == VideoStatus.PROCESSING.value:
                    analytics["processing_videos"] = count
                elif status == VideoStatus.FAILED.value:
                    analytics["failed_videos"] = count
                elif status == VideoStatus.PENDING.value:
                    analytics["pending_videos"] = count

            return analytics

        except Exception as e:
            logger.error(f"Failed to get video analytics: {e}")
            raise VideoProcessingException(f"Failed to get video analytics: {str(e)}")

    async def search_videos(
        self, user_id: str, search_term: str, page: int = 1, per_page: int = 10
    ) -> Dict[str, Any]:
        """Search videos by title or metadata"""
        try:
            query = {
                "user_id": user_id,
                "is_deleted": {"$ne": True},
                "$or": [
                    {"title": {"$regex": search_term, "$options": "i"}},
                    {"metadata.description": {"$regex": search_term, "$options": "i"}},
                    {"metadata.keywords": {"$in": [search_term]}},
                ],
            }

            # Count total documents
            total_count = await self.collection.count_documents(query)

            # Calculate skip value
            skip = (page - 1) * per_page
            total_pages = -(-total_count // per_page)  # Ceiling division

            # Get videos with pagination
            cursor = (
                self.collection.find(query)
                .sort("created_at", -1)
                .skip(skip)
                .limit(per_page)
            )

            videos = []
            async for video in cursor:
                video["_id"] = str(video["_id"])
                videos.append(video)

            return {
                "videos": videos,
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
            }

        except Exception as e:
            logger.error(f"Failed to search videos: {e}")
            raise VideoProcessingException(f"Failed to search videos: {str(e)}")

    # Enhanced video generation methods from python-backend

    async def generate_video_clips_details(
        self,
        video_data: Dict[str, Any],
        script_data: Dict[str, Any],
        percentage: int = 2,
    ) -> Dict[str, Any]:
        """Generate video clips details for video processing"""
        try:
            video_id = str(video_data["_id"])
            video_link = script_data.get("video_link")
            video_file_path = video_data.get("video_file_path")

            if script_data.get("type") == "VIDEO":
                if video_data.get("video_clips_details") is None:
                    # This would integrate with video processing service
                    # For now, return mock data
                    video_clips_details = {
                        "clips": [
                            {
                                "start_time": 0,
                                "end_time": 10,
                                "description": "Opening scene",
                                "relevance_score": 8.5,
                            }
                        ]
                    }

                    update_data = {
                        "video_clips_details": video_clips_details,
                        "video_file_path": video_file_path,
                    }

                    video_data = await self.update_video(video_id, update_data)

            return video_data

        except Exception as e:
            logger.error(f"Error generating video clips details: {e}")
            raise VideoProcessingException(f"Failed to generate clips: {str(e)}")

    async def process_script_for_video(
        self,
        script_data: Dict[str, Any],
        video_data: Dict[str, Any],
        audio_data: Dict[str, Any],
        video_file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process script data for video generation"""
        try:
            video_id = str(video_data["_id"])
            user_id = str(video_data["user_id"])

            # Generate stock video clips if needed
            if (
                video_data.get("stock_video_clips") is None
                or len(video_data.get("stock_video_clips", [])) == 0
            ):

                # Generate search terms and fetch stock videos
                search_terms_data = await self.generate_search_terms(
                    script_data["content"], audio_data.get("subtitles", [])
                )

                stock_clips, video_urls = await self.fetch_stock_videos(
                    video_id, search_terms_data
                )

                video_data = await self.update_video(
                    video_id,
                    {"stock_video_clips": stock_clips, "video_urls": video_urls},
                )

            # Generate images if needed
            if (
                video_data.get("images") is None
                or len(video_data.get("images", [])) == 0
            ):

                image_data = await self.generate_images_for_video(
                    video_id,
                    script_data["title"],
                    script_data["content"],
                    audio_data.get("subtitles", []),
                )

                video_data = await self.update_video(video_id, {"images": image_data})

            return video_data

        except Exception as e:
            logger.error(f"Error processing script for video: {e}")
            raise VideoProcessingException(f"Failed to process script: {str(e)}")

    async def generate_search_terms(
        self, script: str, subtitles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate search terms for stock video/image search"""
        try:
            # This would integrate with AI service to generate search terms
            # For now, return mock data
            search_terms = {
                "data": [
                    {
                        "search_terms": "technology innovation",
                        "at_time": 0,
                        "duration": 5,
                    },
                    {"search_terms": "business growth", "at_time": 5, "duration": 5},
                ]
            }

            return search_terms

        except Exception as e:
            logger.error(f"Error generating search terms: {e}")
            return {"data": []}

    async def fetch_stock_videos(
        self, video_id: str, search_terms_data: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Fetch stock videos based on search terms"""
        try:
            video_urls = []
            processed_clips = []

            for term_data in search_terms_data.get("data", []):
                search_term = term_data["search_terms"]

                # This would integrate with stock video APIs
                # For now, return mock URLs
                mock_url = f"https://example.com/stock/{uuid.uuid4()}.mp4"
                video_urls.append(mock_url)

                processed_clips.append(
                    {**term_data, "url": mock_url, "relevance_score": 7.5}
                )

            return processed_clips, video_urls

        except Exception as e:
            logger.error(f"Error fetching stock videos: {e}")
            return [], []

    async def generate_images_for_video(
        self, video_id: str, title: str, script: str, subtitles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate images for video"""
        try:
            # This would integrate with image generation service
            # For now, return mock data
            images = [
                {
                    "url": f"https://example.com/image/{uuid.uuid4()}.jpg",
                    "atTime": 0,
                    "duration": 3,
                    "description": "Opening image",
                },
                {
                    "url": f"https://example.com/image/{uuid.uuid4()}.jpg",
                    "atTime": 10,
                    "duration": 3,
                    "description": "Supporting image",
                },
            ]

            return images

        except Exception as e:
            logger.error(f"Error generating images: {e}")
            return []

    async def generate_video_with_workflow(
        self, video_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate video using complete workflow"""
        try:
            video_id = str(video_data["_id"])
            user_id = str(video_data["user_id"])
            script_id = str(video_data["script_id"])

            # Get script data
            script_data = await self.get_script_data(script_id)
            if not script_data:
                raise VideoNotFoundException("Script not found")

            # Generate audio data (mock)
            audio_data = await self.generate_audio_data(script_data)

            # Generate video clips details
            video_data = await self.generate_video_clips_details(
                video_data, script_data
            )

            # Process script for video generation
            video_data = await self.process_script_for_video(
                script_data, video_data, audio_data
            )

            # Update video status
            video_data = await self.update_video(
                video_id,
                {
                    "status": VideoStatus.PROCESSING.value,
                    "status_message": "Video generation in progress",
                },
            )

            # Send to video generation queue (mock)
            await self.queue_video_generation(video_id)

            return video_data

        except Exception as e:
            logger.error(f"Error generating video with workflow: {e}")
            raise VideoProcessingException(f"Failed to generate video: {str(e)}")

    async def get_script_data(self, script_id: str) -> Optional[Dict[str, Any]]:
        """Get script data by ID"""
        try:
            # This would integrate with script service
            # For now, return mock data
            return {
                "_id": script_id,
                "title": "Sample Script",
                "content": "This is a sample script content",
                "type": "TOPIC",
            }

        except Exception as e:
            logger.error(f"Error getting script data: {e}")
            return None

    async def generate_audio_data(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audio data from script"""
        try:
            # This would integrate with audio generation service
            # For now, return mock data
            return {
                "_id": str(ObjectId()),
                "audio_links": [f"https://example.com/audio/{uuid.uuid4()}.mp3"],
                "subtitles": [{"text": "Sample subtitle text", "start": 0, "end": 5}],
            }

        except Exception as e:
            logger.error(f"Error generating audio data: {e}")
            return {}

    async def queue_video_generation(self, video_id: str) -> bool:
        """Queue video for generation processing"""
        try:
            # This would integrate with task queue system
            # For now, just log the action
            logger.info(f"Queued video {video_id} for generation")

            # Send progress update via Redis
            await self.send_progress_update(video_id, "Video queued for processing", 10)

            return True

        except Exception as e:
            logger.error(f"Error queuing video generation: {e}")
            return False

    async def send_progress_update(self, video_id: str, message: str, progress: int):
        """Send progress update via Redis"""
        try:
            update_data = {
                "video_id": video_id,
                "message": message,
                "progress": progress,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Send to Redis channel
            channel = f"video_progress:{video_id}"
            redis_service.publish(channel, json.dumps(update_data))

        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

    async def download_video_with_quality(
        self, user_id: str, video_data: Dict[str, Any], quality: str
    ) -> Dict[str, str]:
        """Download video with specific quality"""
        try:
            video_id = str(video_data["_id"])

            if not video_data.get("link"):
                raise VideoProcessingException("Video is not available")

            if quality == "720p":
                download_link = video_data["link"]
            elif quality == "1080p":
                if video_data.get("link_1080p"):
                    download_link = video_data["link_1080p"]
                else:
                    # Generate 1080p version
                    download_link = await self.generate_hd_version(video_data)
            else:
                raise VideoProcessingException("Video quality not available")

            return {"download_link": download_link}

        except Exception as e:
            logger.error(f"Error downloading video with quality: {e}")
            raise VideoProcessingException(f"Failed to download video: {str(e)}")

    async def generate_hd_version(self, video_data: Dict[str, Any]) -> str:
        """Generate HD version of video"""
        try:
            video_id = str(video_data["_id"])

            # This would integrate with video processing service
            # For now, return mock HD link
            hd_link = f"https://example.com/hd/{video_id}_1080p.mp4"

            # Update video with HD link
            await self.update_video(video_id, {"link_1080p": hd_link})

            return hd_link

        except Exception as e:
            logger.error(f"Error generating HD version: {e}")
            raise VideoProcessingException(f"Failed to generate HD version: {str(e)}")

    async def upload_video_to_platform(
        self, user_id: str, video_data: Dict[str, Any], platform: str
    ) -> Dict[str, Any]:
        """Upload video to external platform"""
        try:
            video_id = str(video_data["_id"])

            # This would integrate with platform APIs (YouTube, LinkedIn, etc.)
            upload_result = {
                "platform": platform,
                "upload_id": f"{platform}_{video_id}_{uuid.uuid4()}",
                "url": f"https://{platform}.com/video/{video_id}",
                "status": "uploaded",
            }

            # Update video with upload info
            upload_info = video_data.get("upload_info", {})
            upload_info[platform] = upload_result

            await self.update_video(video_id, {"upload_info": upload_info})

            return upload_result

        except Exception as e:
            logger.error(f"Error uploading video to platform: {e}")
            raise VideoProcessingException(f"Failed to upload video: {str(e)}")

    async def regenerate_video(
        self, user_id: str, video_id: str, regeneration_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Regenerate video with new parameters"""
        try:
            video_data = await self.get_video_by_user_id(user_id, video_id)
            if not video_data:
                raise VideoNotFoundException(video_id)

            # Update video with new parameters
            update_data = {
                "status": VideoStatus.PENDING.value,
                "status_message": "Regeneration requested",
                **regeneration_params,
            }

            video_data = await self.update_video(video_id, update_data)

            # Queue for regeneration
            await self.queue_video_generation(video_id)

            return video_data

        except Exception as e:
            logger.error(f"Error regenerating video: {e}")
            raise VideoProcessingException(f"Failed to regenerate video: {str(e)}")
