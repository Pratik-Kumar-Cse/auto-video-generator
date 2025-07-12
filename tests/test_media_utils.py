"""
Unit tests for media utilities
"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
from datetime import datetime
from PIL import Image
import cv2

from app.utils.media_utils import MediaUtils


class TestMediaUtils:
    """Test media utility functions"""

    @pytest.fixture
    def mock_cv2_video(self):
        """Mock CV2 VideoCapture"""
        mock_video = MagicMock()
        mock_video.isOpened.return_value = True
        mock_video.set.return_value = True
        mock_video.read.return_value = (True, MagicMock())
        mock_video.release.return_value = None
        return mock_video

    @pytest.fixture
    def mock_pil_image(self):
        """Mock PIL Image"""
        mock_image = MagicMock(spec=Image.Image)
        mock_image.width = 1920
        mock_image.height = 1080
        mock_image.mode = "RGB"
        mock_image.resize.return_value = mock_image
        mock_image.crop.return_value = mock_image
        mock_image.save.return_value = None
        return mock_image

    def test_generate_thumbnail_success(self, mock_cv2_video):
        """Test successful thumbnail generation"""
        with patch('cv2.VideoCapture', return_value=mock_cv2_video), \
             patch('cv2.cvtColor') as mock_cvtcolor, \
             patch('PIL.Image.fromarray') as mock_fromarray, \
             patch.object(MediaUtils, '_resize_and_crop') as mock_resize:
            
            mock_cvtcolor.return_value = MagicMock()
            mock_pil_image = MagicMock()
            mock_fromarray.return_value = mock_pil_image
            mock_resize.return_value = mock_pil_image
            
            result = MediaUtils.generate_thumbnail(
                "test_video.mp4",
                "thumbnail.jpg",
                time=5.0,
                size=(480, 480)
            )
            
            assert result is True
            mock_cv2_video.set.assert_called_once()
            mock_cv2_video.read.assert_called_once()
            mock_pil_image.save.assert_called_once()

    def test_generate_thumbnail_video_not_opened(self):
        """Test thumbnail generation when video cannot be opened"""
        mock_video = MagicMock()
        mock_video.isOpened.return_value = False
        
        with patch('cv2.VideoCapture', return_value=mock_video):
            result = MediaUtils.generate_thumbnail(
                "invalid_video.mp4",
                "thumbnail.jpg"
            )
            
            assert result is False

    def test_generate_thumbnail_read_frame_failed(self, mock_cv2_video):
        """Test thumbnail generation when frame reading fails"""
        mock_cv2_video.read.return_value = (False, None)
        
        with patch('cv2.VideoCapture', return_value=mock_cv2_video):
            result = MediaUtils.generate_thumbnail(
                "test_video.mp4",
                "thumbnail.jpg"
            )
            
            assert result is False

    def test_generate_thumbnail_exception(self):
        """Test thumbnail generation with exception"""
        with patch('cv2.VideoCapture', side_effect=Exception("CV2 error")):
            result = MediaUtils.generate_thumbnail(
                "test_video.mp4",
                "thumbnail.jpg"
            )
            
            assert result is False

    def test_create_image_thumbnail_success(self, mock_pil_image):
        """Test successful image thumbnail creation"""
        with patch('PIL.Image.open', return_value=mock_pil_image), \
             patch('pathlib.Path') as mock_path, \
             patch.object(MediaUtils, '_resize_and_crop', return_value=mock_pil_image):
            
            mock_path_instance = MagicMock()
            mock_path_instance.stem = "test_image"
            mock_path_instance.suffix = ".jpg"
            mock_path_instance.parent = MagicMock()
            mock_path.return_value = mock_path_instance
            
            result = MediaUtils.create_image_thumbnail(
                "test_image.jpg",
                max_size=(240, 240)
            )
            
            assert result is not None
            mock_pil_image.save.assert_called_once()

    def test_create_image_thumbnail_rgba_conversion(self):
        """Test image thumbnail creation with RGBA to RGB conversion"""
        mock_image = MagicMock()
        mock_image.mode = "RGBA"
        mock_converted = MagicMock()
        mock_image.convert.return_value = mock_converted
        
        with patch('PIL.Image.open', return_value=mock_image), \
             patch('pathlib.Path') as mock_path, \
             patch.object(MediaUtils, '_resize_and_crop', return_value=mock_converted):
            
            mock_path_instance = MagicMock()
            mock_path_instance.stem = "test_image"
            mock_path_instance.suffix = ".png"
            mock_path_instance.parent = MagicMock()
            mock_path.return_value = mock_path_instance
            
            result = MediaUtils.create_image_thumbnail("test_image.png")
            
            assert result is not None
            mock_image.convert.assert_called_once_with("RGB")

    def test_create_image_thumbnail_exception(self):
        """Test image thumbnail creation with exception"""
        with patch('PIL.Image.open', side_effect=Exception("PIL error")):
            result = MediaUtils.create_image_thumbnail("test_image.jpg")
            
            assert result is None

    def test_resize_and_crop_wider_image(self):
        """Test resize and crop for wider image"""
        mock_image = MagicMock()
        mock_image.width = 1920
        mock_image.height = 1080
        mock_resized = MagicMock()
        mock_resized.width = 640
        mock_resized.height = 360
        mock_image.resize.return_value = mock_resized
        
        result = MediaUtils._resize_and_crop(mock_image, (480, 480))
        
        mock_image.resize.assert_called_once()
        mock_resized.crop.assert_called_once()

    def test_resize_and_crop_taller_image(self):
        """Test resize and crop for taller image"""
        mock_image = MagicMock()
        mock_image.width = 1080
        mock_image.height = 1920
        mock_resized = MagicMock()
        mock_resized.width = 360
        mock_resized.height = 640
        mock_image.resize.return_value = mock_resized
        
        result = MediaUtils._resize_and_crop(mock_image, (480, 480))
        
        mock_image.resize.assert_called_once()
        mock_resized.crop.assert_called_once()

    def test_download_video_success(self):
        """Test successful video download"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        
        with patch('requests.get', return_value=mock_response), \
             patch('os.makedirs'), \
             patch('os.path.dirname', return_value="/path/to"), \
             patch('builtins.open', mock_open()) as mock_file:
            
            result = MediaUtils.download_video(
                "https://example.com/video.mp4",
                "/path/to/video.mp4"
            )
            
            assert result is True
            mock_file.assert_called_once()

    def test_download_video_http_error(self):
        """Test video download with HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        
        with patch('requests.get', return_value=mock_response):
            result = MediaUtils.download_video(
                "https://example.com/nonexistent.mp4",
                "/path/to/video.mp4"
            )
            
            assert result is False

    def test_download_video_exception(self):
        """Test video download with exception"""
        with patch('requests.get', side_effect=Exception("Network error")):
            result = MediaUtils.download_video(
                "https://example.com/video.mp4",
                "/path/to/video.mp4"
            )
            
            assert result is False

    def test_get_image_files_default_extensions(self):
        """Test getting image files with default extensions"""
        with patch('pathlib.Path') as mock_path:
            mock_folder = MagicMock()
            mock_folder.glob.side_effect = [
                ["/path/image1.jpg", "/path/image2.png"],
                ["/path/IMAGE3.JPG"]
            ]
            mock_path.return_value = mock_folder
            
            result = MediaUtils.get_image_files("/path/to/images")
            
            assert len(result) > 0
            assert all(isinstance(path, str) for path in result)

    def test_get_image_files_custom_extensions(self):
        """Test getting image files with custom extensions"""
        with patch('pathlib.Path') as mock_path:
            mock_folder = MagicMock()
            mock_folder.glob.return_value = ["/path/image1.webp"]
            mock_path.return_value = mock_folder
            
            result = MediaUtils.get_image_files(
                "/path/to/images",
                extensions=[".webp"]
            )
            
            assert len(result) > 0

    def test_get_audio_files_success(self):
        """Test getting audio files"""
        mock_files = ["audio1.mp3", "audio2.wav", "document.txt"]
        
        with patch('os.listdir', return_value=mock_files), \
             patch('os.path.isfile', side_effect=lambda x: x.endswith(('.mp3', '.wav'))), \
             patch('os.path.splitext', side_effect=lambda x: (x[:-4], x[-4:])):
            
            result = MediaUtils.get_audio_files("/path/to/audio")
            
            assert len(result) == 2
            assert all("audio" in path for path in result)

    def test_get_file_metadata_success(self):
        """Test getting file metadata"""
        mock_stat = MagicMock()
        mock_stat.st_size = 1024
        mock_stat.st_ctime = 1640995200  # 2022-01-01
        mock_stat.st_mtime = 1640995200
        
        with patch('os.stat', return_value=mock_stat), \
             patch('mimetypes.guess_type', return_value=("video/mp4", None)), \
             patch('os.path.basename', return_value="test.mp4"), \
             patch('os.path.splitext', return_value=("test", ".mp4")):
            
            result = MediaUtils.get_file_metadata("/path/to/test.mp4")
            
            assert result["filename"] == "test.mp4"
            assert result["size"] == 1024
            assert result["mime_type"] == "video/mp4"
            assert result["extension"] == ".mp4"
            assert isinstance(result["created_at"], datetime)

    def test_get_file_metadata_audio_with_mutagen(self):
        """Test getting audio file metadata with mutagen"""
        mock_stat = MagicMock()
        mock_stat.st_size = 2048
        mock_stat.st_ctime = 1640995200
        mock_stat.st_mtime = 1640995200
        
        mock_audio = MagicMock()
        mock_audio.info.length = 180.5
        mock_audio.info.bitrate = 320
        
        with patch('os.stat', return_value=mock_stat), \
             patch('mimetypes.guess_type', return_value=("audio/mp3", None)), \
             patch('os.path.basename', return_value="test.mp3"), \
             patch('os.path.splitext', return_value=("test", ".mp3")), \
             patch('mutagen.File', return_value=mock_audio):
            
            result = MediaUtils.get_file_metadata("/path/to/test.mp3")
            
            assert result["duration"] == 180.5
            assert result["bitrate"] == 320

    def test_get_file_metadata_audio_without_mutagen(self):
        """Test getting audio file metadata without mutagen"""
        mock_stat = MagicMock()
        mock_stat.st_size = 2048
        mock_stat.st_ctime = 1640995200
        mock_stat.st_mtime = 1640995200
        
        with patch('os.stat', return_value=mock_stat), \
             patch('mimetypes.guess_type', return_value=("audio/mp3", None)), \
             patch('os.path.basename', return_value="test.mp3"), \
             patch('os.path.splitext', return_value=("test", ".mp3")), \
             patch('mutagen.File', side_effect=ImportError("mutagen not available")):
            
            result = MediaUtils.get_file_metadata("/path/to/test.mp3")
            
            assert "duration" not in result
            assert "bitrate" not in result

    def test_get_file_metadata_exception(self):
        """Test getting file metadata with exception"""
        with patch('os.stat', side_effect=Exception("File not found")), \
             patch('os.path.basename', return_value="test.mp4"):
            
            result = MediaUtils.get_file_metadata("/path/to/test.mp4")
            
            assert result["filename"] == "test.mp4"
            assert "error" in result

    def test_validate_media_file_valid(self):
        """Test validating valid media file"""
        with patch('os.path.exists', return_value=True), \
             patch('mimetypes.guess_type', return_value=("video/mp4", None)):
            
            result = MediaUtils.validate_media_file("/path/to/video.mp4")
            
            assert result is True

    def test_validate_media_file_invalid_type(self):
        """Test validating file with invalid type"""
        with patch('os.path.exists', return_value=True), \
             patch('mimetypes.guess_type', return_value=("text/plain", None)):
            
            result = MediaUtils.validate_media_file("/path/to/document.txt")
            
            assert result is False

    def test_validate_media_file_with_allowed_types(self):
        """Test validating file with specific allowed types"""
        with patch('os.path.exists', return_value=True), \
             patch('mimetypes.guess_type', return_value=("image/jpeg", None)):
            
            result = MediaUtils.validate_media_file(
                "/path/to/image.jpg",
                allowed_types=["image/"]
            )
            
            assert result is True

    def test_validate_media_file_not_exists(self):
        """Test validating non-existent file"""
        with patch('os.path.exists', return_value=False):
            result = MediaUtils.validate_media_file("/path/to/nonexistent.mp4")
            
            assert result is False

    def test_validate_media_file_no_mime_type(self):
        """Test validating file with no mime type"""
        with patch('os.path.exists', return_value=True), \
             patch('mimetypes.guess_type', return_value=(None, None)):
            
            result = MediaUtils.validate_media_file("/path/to/unknown")
            
            assert result is False

    def test_validate_media_file_exception(self):
        """Test validating file with exception"""
        with patch('os.path.exists', side_effect=Exception("Permission denied")):
            result = MediaUtils.validate_media_file("/path/to/video.mp4")
            
            assert result is False

    def test_cleanup_temp_files_success(self):
        """Test successful cleanup of temp files"""
        current_time = 1640995200  # 2022-01-01
        old_file_time = 1640908800  # 2021-12-31 (1 day old)
        recent_file_time = 1640991600  # 2022-01-01 (1 hour old)
        
        mock_files = ["old_file.tmp", "recent_file.tmp"]
        
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=mock_files), \
             patch('os.path.isfile', return_value=True), \
             patch('os.path.getmtime', side_effect=[old_file_time, recent_file_time]), \
             patch('datetime.datetime.now') as mock_now, \
             patch('os.remove') as mock_remove:
            
            mock_now.return_value.timestamp.return_value = current_time
            
            MediaUtils.cleanup_temp_files("/tmp", max_age_hours=12)
            
            # Only old file should be removed
            mock_remove.assert_called_once_with("/tmp/old_file.tmp")

    def test_cleanup_temp_files_directory_not_exists(self):
        """Test cleanup when temp directory doesn't exist"""
        with patch('os.path.exists', return_value=False):
            # Should not raise exception
            MediaUtils.cleanup_temp_files("/nonexistent")

    def test_cleanup_temp_files_exception(self):
        """Test cleanup with exception"""
        with patch('os.path.exists', return_value=True), \
             patch('os.listdir', side_effect=Exception("Permission denied")):
            
            # Should not raise exception
            MediaUtils.cleanup_temp_files("/tmp")

    def test_resize_and_crop_edge_cases(self):
        """Test resize and crop with edge cases"""
        # Square image
        mock_image = MagicMock()
        mock_image.width = 1000
        mock_image.height = 1000
        mock_resized = MagicMock()
        mock_resized.width = 480
        mock_resized.height = 480
        mock_image.resize.return_value = mock_resized
        
        result = MediaUtils._resize_and_crop(mock_image, (480, 480))
        
        mock_image.resize.assert_called_once()
        mock_resized.crop.assert_called_once()

    def test_get_audio_files_empty_directory(self):
        """Test getting audio files from empty directory"""
        with patch('os.listdir', return_value=[]):
            result = MediaUtils.get_audio_files("/empty/directory")
            
            assert result == []

    def test_get_image_files_no_matches(self):
        """Test getting image files when no matches found"""
        with patch('pathlib.Path') as mock_path:
            mock_folder = MagicMock()
            mock_folder.glob.return_value = []
            mock_path.return_value = mock_folder
            
            result = MediaUtils.get_image_files("/path/with/no/images")
            
            assert result == []

    def test_download_video_large_file(self):
        """Test downloading large video file in chunks"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Simulate large file with multiple chunks
        mock_response.iter_content.return_value = [b"chunk"] * 1000
        
        with patch('requests.get', return_value=mock_response), \
             patch('os.makedirs'), \
             patch('os.path.dirname', return_value="/path/to"), \
             patch('builtins.open', mock_open()) as mock_file:
            
            result = MediaUtils.download_video(
                "https://example.com/large_video.mp4",
                "/path/to/large_video.mp4"
            )
            
            assert result is True
            # Verify file was written in chunks
            handle = mock_file.return_value.__enter__.return_value
            assert handle.write.call_count == 1000