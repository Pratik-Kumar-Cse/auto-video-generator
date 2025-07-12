from moviepy.editor import VideoFileClip
from typing import Annotated
import json
import os
import subprocess

import numpy as np
import PIL

PIL.Image.ANTIALIAS = PIL.Image.LANCZOS


def create_thumbnail(video_path, output_path, time=20):
    """
    Create a thumbnail image from a video file.

    :param video_path: Path to the input video file
    :param output_path: Path to save the output thumbnail image
    :param time: Time in seconds at which to extract the thumbnail (default is 0, the first frame)
    """
    try:

        # Load the video clip
        video = VideoFileClip(video_path)

        width, height = video.size

        video = video.resize((width / 2, height / 2))

        # Save the frame as an image
        video.save_frame(output_path, t=time)

        print(f"Thumbnail created successfully: {output_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Make sure to close the video to free up resources
        video.close()


def create_and_save_clips(
    clip_timestamps: Annotated[list, "list of sub clips time"],
    video_path: Annotated[str, "string of video path"],
    video_id: Annotated[str, "string of video id"],
) -> Annotated[str, "successfully"]:
    """
    Create and save multiple clips from a video by passing the clip's timestamp.

    Args:
        video_file (str): The path to the video file.
        clip_timestamps (list): A list of tuples containing the start and end timestamps for each clip.

    Returns:
        None
    """

    new_clips = []

    with open("./content/clips.json", "r") as file:
        data = json.load(file)

    for key, value in data.items():
        clips = json.loads(key)

    clips = sorted(clips, key=lambda x: x["clip"])

    for index, clip in enumerate(clips):

        if clip["clip"] > len(clip_timestamps):
            break

        new_clips.append(
            {
                "clip": clip["clip"],
                "atTime": clip["atTime"],
                "background_placement": clip["background_placement"],
                "clip_duration": clip_timestamps[clip["clip"] - 1],
            }
        )

    data = {"data": new_clips}

    with open("./content/clips.json", "w") as json_file:
        json.dump(data, json_file)

    return "success"


def convert_video_to_audio(input_video_file, output_audio_file) -> str:
    with VideoFileClip(input_video_file) as video:
        audio = video.audio
        audio.write_audiofile(
            output_audio_file,
            codec="libmp3lame",
            bitrate="128k",
            ffmpeg_params=["-q:a", "0"],
        )
    return output_audio_file


def stop_ffmpeg_processes():
    if os.name == "nt":
        # Windows
        try:
            subprocess.run(["taskkill", "/f", "/im", "ffmpeg.exe"], check=True)
        except subprocess.CalledProcessError:
            print("Failed to stop FFMPEG processes on Windows.")
    # else:
    #     # Other OS
    #     try:
    #         subprocess.run(["killall", "ffmpeg"], check=True)
    #     except subprocess.CalledProcessError:
    #         print("Failed to stop FFMPEG processes on this operating system.")


def add_zoom_effect(clip, start_time, end_time, zoom_type="in", zoom_factor=1.5):
    """
    Add a zoom in or zoom out effect to a video clip.

    Parameters:
    -----------
    clip : VideoClip
        The video clip to apply the zoom effect to
    start_time : float
        Time in seconds when the zoom effect should start
    end_time : float
        Time in seconds when the zoom effect should end
    zoom_type : str, optional
        Type of zoom: "in" to zoom in or "out" to zoom out (default: "in")
    zoom_factor : float, optional
        Maximum zoom factor (default: 1.5)
        For zoom in: starts at 1.0, ends at zoom_factor
        For zoom out: starts at zoom_factor, ends at 1.0

    Returns:
    --------
    VideoClip
        New video clip with the zoom effect applied
    """
    # Original clip dimensions
    w, h = clip.size

    # Validate inputs
    if start_time < 0 or end_time > clip.duration or start_time >= end_time:
        raise ValueError("Invalid time range")

    if zoom_type not in ["in", "out"]:
        raise ValueError("zoom_type must be either 'in' or 'out'")

    if zoom_factor <= 0:
        raise ValueError("zoom_factor must be positive")

    # Define the zoom function
    def zoom_effect(get_frame, t):
        # Get the current frame
        frame = get_frame(t)

        # If outside the zoom time range, return the original frame
        if t < start_time or t > end_time:
            return frame

        # Calculate current zoom progress (0 to 1)
        progress = (t - start_time) / (end_time - start_time)

        # Calculate current zoom scale based on zoom type
        if zoom_type == "in":
            # For zoom in: scale goes from 1.0 to zoom_factor
            scale = 1.0 + progress * (zoom_factor - 1.0)
        else:  # zoom out
            # For zoom out: scale goes from zoom_factor to 1.0
            scale = zoom_factor - progress * (zoom_factor - 1.0)

        # Calculate new dimensions
        new_w = int(w * scale)
        new_h = int(h * scale)

        # Resize the frame
        import cv2

        resized_frame = cv2.resize(
            frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR
        )

        # Calculate the center crop
        x_center = new_w // 2
        y_center = new_h // 2

        x1 = max(0, x_center - w // 2)
        y1 = max(0, y_center - h // 2)
        x2 = min(new_w, x_center + w // 2)
        y2 = min(new_h, y_center + h // 2)

        # Crop the frame to original dimensions
        cropped_frame = resized_frame[y1:y2, x1:x2]

        # Handle edge cases where the cropped frame might be smaller than original dimensions
        if cropped_frame.shape[0] < h or cropped_frame.shape[1] < w:
            result = np.zeros((h, w, 3), dtype=np.uint8)
            # Calculate the position to place the cropped frame
            y_offset = (h - cropped_frame.shape[0]) // 2
            x_offset = (w - cropped_frame.shape[1]) // 2
            result[
                y_offset : y_offset + cropped_frame.shape[0],
                x_offset : x_offset + cropped_frame.shape[1],
            ] = cropped_frame
            return result

        return cropped_frame

    # Apply the zoom effect
    zoomed_clip = clip.fl(lambda gf, t: zoom_effect(gf, t))

    return zoomed_clip
