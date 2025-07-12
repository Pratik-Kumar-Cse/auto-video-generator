from moviepy.editor import VideoFileClip
from typing import Annotated
import json
import os
import subprocess


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
