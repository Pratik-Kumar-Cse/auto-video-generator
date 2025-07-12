import subprocess
import os
from app.constant.constant import VIDEO_RESOLUTIONS
from app.constant.video_enums import VideoRatioValues
from ..utils import create_directory


def generate_resolutions(input_path, output_paths, resolutions, aspect_ratio="16:9"):
    """
    Generate videos in multiple resolutions with specified aspect ratio using FFmpeg.

    Args:
    - input_path: Path to the input video.
    - output_paths: List of output file paths.
    - resolutions: List of resolutions as tuples (width, height).
    - aspect_ratio: Desired aspect ratio, e.g., "1:1" or "9:16".
    """
    for output_path, resolution in zip(output_paths, resolutions):

        if not os.path.exists(output_path):
            width, height = resolution

            # Adjust scale and padding for the aspect ratio
            if aspect_ratio == "1:1":  # Square video
                scale_filter = f"scale={width}:{width}:force_original_aspect_ratio=decrease,pad={width}:{width}:(ow-iw)/2:(oh-ih)/2"
            elif aspect_ratio == "9:16":  # Portrait video
                scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
            else:  # Default 16:9 landscape
                scale_filter = f"scale={width}:{height}"

            command = [
                "ffmpeg",
                "-i",
                input_path,  # Input file
                "-vf",
                scale_filter,  # Set the scale and padding for aspect ratio
                "-c:v",
                "libx264",  # Use H.264 codec for video
                "-preset",
                "slow",  # Encoding preset
                "-crf",
                "23",  # Constant rate factor (lower is better quality)
                "-c:a",
                "aac",  # Use AAC codec for audio
                "-b:a",
                "128k",  # Audio bitrate
                output_path,  # Output file path
            ]
            subprocess.run(command, check=True)  # Run the FFmpeg command


def convert_video(video_id, video_resolution):
    try:
        video_resolutions = VIDEO_RESOLUTIONS.get(video_resolution)

        aspect_ratio = VideoRatioValues[video_resolution.upper()].value

        compressed_directory = f"./temp/{video_id}/compressed"
        create_directory(compressed_directory)

        # Get output paths based on the selected resolution
        output_paths = [
            f"{compressed_directory}/video_{res[0]}x{res[1]}.mp4"
            for res in video_resolutions
        ]

        input_video = f"./temp/{video_id}/{video_id}.mp4"

        # Generate videos for the selected resolutions
        generate_resolutions(input_video, output_paths, video_resolutions, aspect_ratio)
    except Exception as e:
        print(f"Error converting a video: {str(e)}")
        raise e
