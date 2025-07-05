"""
Media utility functions for video processing, thumbnail generation, and file uploads
Enhanced from python-backend/script.py functionality
"""

import os
import cv2
import requests
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class MediaUtils:
    """Utility class for media processing operations"""

    @staticmethod
    def generate_thumbnail(
        video_path: str, 
        output_path: str, 
        time: float = 0.0,
        size: Tuple[int, int] = (480, 480)
    ) -> bool:
        """
        Generate a thumbnail from a video file
        
        Args:
            video_path: Path to the video file
            output_path: Path where thumbnail will be saved
            time: Time in seconds to capture frame from
            size: Thumbnail size (width, height)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Open the video file
            video = cv2.VideoCapture(video_path)
            
            if not video.isOpened():
                logger.error(f"Could not open video file: {video_path}")
                return False

            # Set the frame position to the specified time
            video.set(cv2.CAP_PROP_POS_MSEC, time * 1000)

            # Read the frame
            success, image = video.read()

            if success:
                # Convert the image from BGR to RGB
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # Create a PIL Image
                pil_image = Image.fromarray(image_rgb)

                # Resize and crop to desired size
                pil_image = MediaUtils._resize_and_crop(pil_image, size)

                # Save the thumbnail
                pil_image.save(output_path, "JPEG", quality=85, optimize=True)
                logger.info(f"Thumbnail generated: {output_path}")
                
                video.release()
                return True
            else:
                logger.error(f"Failed to read frame from {video_path}")
                video.release()
                return False

        except Exception as e:
            logger.error(f"Error generating thumbnail: {e}")
            return False

    @staticmethod
    def create_image_thumbnail(
        image_path: str, 
        max_size: Tuple[int, int] = (240, 240)
    ) -> Optional[str]:
        """
        Create a thumbnail from an image file
        
        Args:
            image_path: Path to the original image
            max_size: Maximum width and height for thumbnail
            
        Returns:
            str: Path to the created thumbnail, None if failed
        """
        try:
            img_path = Path(image_path)
            
            with Image.open(img_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Resize and crop
                img = MediaUtils._resize_and_crop(img, max_size)

                # Generate thumbnail filename
                thumb_filename = f"{img_path.stem}_thumb{img_path.suffix}"
                thumb_path = img_path.parent / thumb_filename

                # Save thumbnail
                img.save(thumb_path, "JPEG", quality=85, optimize=True)
                return str(thumb_path)

        except Exception as e:
            logger.error(f"Error creating image thumbnail for {image_path}: {e}")
            return None

    @staticmethod
    def _resize_and_crop(image: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize and crop image to target size maintaining aspect ratio
        
        Args:
            image: PIL Image object
            target_size: Target (width, height)
            
        Returns:
            PIL Image object
        """
        width, height = target_size
        aspect_ratio = image.width / image.height
        
        if aspect_ratio > 1:
            # Image is wider than tall
            new_width = int(width * aspect_ratio)
            new_height = height
        else:
            # Image is taller than wide
            new_width = width
            new_height = int(height / aspect_ratio)

        # Resize maintaining aspect ratio
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate coordinates for center crop
        left = (image.width - width) // 2
        top = (image.height - height) // 2
        right = left + width
        bottom = top + height

        # Crop to target size
        return image.crop((left, top, right, bottom))

    @staticmethod
    def download_video(url: str, output_path: str) -> bool:
        """
        Download a video from URL
        
        Args:
            url: Video URL
            output_path: Local path to save video
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video downloaded: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading video from {url}: {e}")
            return False

    @staticmethod
    def get_image_files(folder_path: str, extensions: List[str] = None) -> List[str]:
        """
        Get all image file paths from a folder
        
        Args:
            folder_path: Path to the folder
            extensions: List of extensions to search for
            
        Returns:
            List of image file paths
        """
        if extensions is None:
            extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        
        folder = Path(folder_path)
        image_files = []
        
        for ext in extensions:
            image_files.extend(folder.glob(f"*{ext}"))
            image_files.extend(folder.glob(f"*{ext.upper()}"))
        
        return [str(path) for path in image_files]

    @staticmethod
    def get_audio_files(folder_path: str, extensions: List[str] = None) -> List[str]:
        """
        Get all audio file paths from a folder
        
        Args:
            folder_path: Path to the folder
            extensions: List of extensions to search for
            
        Returns:
            List of audio file paths
        """
        if extensions is None:
            extensions = [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"]
        
        folder = Path(folder_path)
        audio_files = []
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if (os.path.isfile(file_path) and 
                os.path.splitext(filename)[1].lower() in extensions):
                audio_files.append(file_path)
        
        return audio_files

    @staticmethod
    def get_file_metadata(file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            metadata = {
                "filename": os.path.basename(file_path),
                "size": stat.st_size,
                "mime_type": mime_type,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "extension": os.path.splitext(file_path)[1].lower()
            }
            
            # Try to get audio metadata if it's an audio file
            if mime_type and mime_type.startswith("audio/"):
                try:
                    from mutagen import File
                    audio = File(file_path)
                    if audio and hasattr(audio, "info"):
                        metadata["duration"] = audio.info.length
                        if hasattr(audio.info, "bitrate"):
                            metadata["bitrate"] = audio.info.bitrate
                except ImportError:
                    logger.warning("Mutagen not available for audio metadata")
                except Exception as e:
                    logger.warning(f"Could not extract audio metadata: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting file metadata for {file_path}: {e}")
            return {"filename": os.path.basename(file_path), "error": str(e)}

    @staticmethod
    def validate_media_file(file_path: str, allowed_types: List[str] = None) -> bool:
        """
        Validate if a file is a valid media file
        
        Args:
            file_path: Path to the file
            allowed_types: List of allowed MIME types
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                return False
            
            if allowed_types:
                return any(mime_type.startswith(t) for t in allowed_types)
            
            # Default: allow common media types
            return mime_type.startswith(("image/", "video/", "audio/"))
            
        except Exception as e:
            logger.error(f"Error validating media file {file_path}: {e}")
            return False

    @staticmethod
    def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24):
        """
        Clean up temporary files older than specified age
        
        Args:
            temp_dir: Directory containing temporary files
            max_age_hours: Maximum age in hours before deletion
        """
        try:
            if not os.path.exists(temp_dir):
                return
            
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Cleaned up temp file: {file_path}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")