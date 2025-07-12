import numpy as np
import os
import random
import sys
import multiprocessing
from functools import lru_cache
from collections import defaultdict
from app.loggers.progress_logger import ProgressLogger
from typing import List
from moviepy.editor import *
from termcolor import colored

from moviepy.video.fx.all import crop
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    clips_array,
    CompositeVideoClip,
    VideoClip,
    CompositeAudioClip,
)
from moviepy.video.VideoClip import TextClip


from .transition import (
    fade,
    add_effect_transition,
    add_zoom_transition,
    add_animation_transition,
    add_burn_transition,
    cross_dissolve,
    add_zoom_in_transition,
    add_zoom_out_transition,
)


from .video_edit import (
    circle_masks,
    circle_mask_with_margin,
    create_rounded_rectangle_mask,
)

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Caching function
def cached_operation(func):
    @lru_cache(maxsize=None)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@cached_operation
def create_logo(
    final_clip,
    logo_path,
    position="top-right",
    margin=40,
    size="medium",
    custom_scale=None,
):
    """
    Create and position a logo on a video clip with dynamic sizing.

    Args:
        final_clip: The video clip to add the logo to
        logo_path: Path to the logo image file
        position: Where to place the logo - 'top-left', 'top-right', 'bottom-left', or 'bottom-right'
        margin: Margin from the edges in pixels (default: 40)
        size: Preset size options - 'small', 'medium', 'large', or 'custom'
        custom_scale: Custom scale factor relative to video height (0.0 to 1.0)
                     Only used when size='custom'

    Returns:
        tuple: (logo_clip, position_tuple)
    """
    # Load logo
    logo = ImageClip(logo_path, duration=final_clip.duration)

    # Calculate video dimensions
    video_height = final_clip.h

    # Define size presets as percentages of video height
    size_factors = {
        "small": 0.04,  # 4% of video height
        "medium": 0.06,  # 6% of video height
        "large": 0.08,  # 8% of video height
    }

    # Determine scaling factor
    if size == "custom" and custom_scale is not None:
        if not 0 < custom_scale <= 1:
            raise ValueError("custom_scale must be between 0 and 1")
        scale_factor = custom_scale
    elif size in size_factors:
        scale_factor = size_factors[size]
    else:
        raise ValueError("Size must be one of: 'small', 'medium', 'large', 'custom'")

    # Calculate target height and maintain aspect ratio
    target_height = int(video_height * scale_factor)
    aspect_ratio = logo.w / logo.h
    target_width = int(target_height * aspect_ratio)

    # Resize logo
    logo = logo.resize(width=target_width, height=target_height)

    # Calculate position based on selected corner
    if position == "top-left":
        logo_pos = (margin, margin)
    elif position == "top-right":
        logo_pos = (final_clip.w - logo.w - margin, margin)
    elif position == "bottom-left":
        logo_pos = (margin, final_clip.h - logo.h - margin)
    elif position == "bottom-right":
        logo_pos = (final_clip.w - logo.w - margin, final_clip.h - logo.h - margin)
    else:
        raise ValueError(
            "Position must be one of: 'top-left', 'top-right', 'bottom-left', 'bottom-right'"
        )

    return logo, logo_pos


def combine_videos(
    video_paths: List[str], max_duration: int, max_clip_duration: int, threads: int
) -> str:
    """
    Combines a list of videos into one video and returns the path to the combined video.

    Args:
        video_paths (List): A list of paths to the videos to combine.
        max_duration (int): The maximum duration of the combined video.
        max_clip_duration (int): The maximum duration of each clip.
        threads (int): The number of threads to use for the video processing.

    Returns:
        str: The path to the combined video.
    """
    # Required duration of each clip
    req_dur = max_duration / len(video_paths)

    print(colored("[+] Combining videos...", "blue"))
    print(colored(f"[+] Each clip will be maximum {req_dur} seconds long.", "blue"))

    clips = []
    tot_dur = 0

    # Add downloaded clips over and over until the duration of the audio (max_duration) has been reached
    while tot_dur < max_duration:
        for video_path in video_paths:
            clip = VideoFileClip(video_path)
            clip = clip.without_audio()
            # Check if clip is longer than the remaining audio
            if (max_duration - tot_dur) < clip.duration:
                clip = clip.subclip(2, 2 + (max_duration - tot_dur))
            # Only shorten clips if the calculated clip length (req_dur) is shorter than the actual clip to prevent still image
            elif req_dur < clip.duration:
                clip = clip.subclip(2, 2 + req_dur)
            clip = clip.set_fps(30)

            # Not all videos are same size,
            # so we need to resize them
            if round((clip.w / clip.h), 4) < 0.4625:
                clip = crop(
                    clip,
                    width=clip.w,
                    height=round(clip.w / 0.4625),
                    x_center=clip.w / 2,
                    y_center=clip.h / 2,
                )
            else:
                clip = crop(
                    clip,
                    width=round(0.4625 * clip.h),
                    height=clip.h,
                    x_center=clip.w / 2,
                    y_center=clip.h / 2,
                )

            clip = clip.resize((540, 960))

            if clip.duration > max_clip_duration:
                clip = clip.subclip(0, max_clip_duration)

            clips.append(clip)
            tot_dur += clip.duration

    final_clip = concatenate_videoclips(clips)
    final_clip = final_clip.set_fps(30)

    final_clip.write_videofile("./output/combine.mp4", threads=threads or 2)
    return final_clip


def combine_two_videos(video1, video2):

    clip1 = video1.crop(x1=100, y1=0, x2=1180, y2=720).resize(newsize=(1080, 960))

    clip2 = video2

    clip1 = clip1.set_duration(clip2.duration)

    # Get the video dimensions
    video_width, video_height = clip2.size

    # Calculate the coordinates for cropping
    x1 = (video_width - 500) // 2
    y1 = (video_height - 530) // 2
    x2 = x1 + 550
    y2 = y1 + 530

    clip2 = clip2.crop(x1=x1, y1=y1, x2=x2, y2=y2).resize(newsize=(1080, 960))

    # Stack the resized video clips on top of each other
    final_clip = clips_array([[clip1], [clip2]])

    final_clip = final_clip.resize(newsize=(1080, 1920))

    return final_clip


def generate_final_video(
    combined_video_clip: str,
    custom_video_path: str,
    subtitles_path: str,
    threads: int,
    subtitles_position: str,
    text_color: str,
    templates: str,
    video_paths,
) -> str:
    """
    This function creates the final video, with subtitles and audio.

    Args:
        combined_video_path (str): The path to the combined video.
        custom_video_path (str): The path to the custom video.
        subtitles_path (str): The path to the subtitles.
        threads (int): The number of threads to use for the video processing.
        subtitles_position (str): The position of the subtitles.
        text_color (str): The color of the subtitles text.

    Returns:
        str: The path to the final video.
    """

    final_clip = None
    output_path = "./output/rapid_video.mp4"

    custom_video = VideoFileClip(custom_video_path)

    if templates == "temp3":
        # Write the stacked clips to a temporary file
        final_clip = add_clips_between_videos(custom_video, video_paths)
        output_path = "./output/reel_temp3.mp4"

    elif templates == "temp2":
        # Write the stacked clips to a temporary file
        final_clip = masking_video(video1=combined_video_clip, video2=custom_video)

        output_path = "./output/reel_temp2.mp4"

    else:
        # Write the stacked clips to a temporary file
        final_clip = combine_two_videos(video1=combined_video_clip, video2=custom_video)

        output_path = "./output/reel_temp1.mp4"

    # Define a generator for creating TextClip objects
    generator = lambda txt: TextClip(
        txt=txt.upper(),
        font="./asset/font/poppins-black.ttf",
        fontsize=80,
        color=text_color,
        stroke_color="black",
        stroke_width=5,
    )

    # Extract the subtitles position
    horizontal_subtitles_position, vertical_subtitles_position = (
        subtitles_position.split(",")
    )

    # Create a SubtitlesClip object
    subtitles = SubtitlesClip(subtitles_path, generator)

    # Composite the main video with the subtitles
    result = CompositeVideoClip(
        [
            final_clip,
            subtitles.set_position(
                (horizontal_subtitles_position, vertical_subtitles_position),
                relative=True,
            ),
        ]
    )

    video2 = VideoFileClip("./asset/data/rapid-outro.mp4")

    # Get the video dimensions
    width, height = video2.size

    # Calculate the aspect ratio of the input video
    aspect_ratio = width / height

    # Desired aspect ratio for reels/shorts
    target_aspect_ratio = 9 / 16

    if aspect_ratio > target_aspect_ratio:
        # Video is wider than the target aspect ratio
        new_width = int(height * target_aspect_ratio)
        x1 = (width - new_width) // 2
        x2 = x1 + new_width
        y1 = 0
        y2 = height
    else:
        # Video is taller than the target aspect ratio
        new_height = int(width / target_aspect_ratio)
        x1 = 0
        x2 = width
        y1 = (height - new_height) // 2
        y2 = y1 + new_height

    # Crop the video to the target aspect ratio
    video2 = crop(video2, x1=x1, y1=y1, x2=x2, y2=y2)

    video2 = video2.resize(width=result.w, height=result.h)

    # Concatenate the resized main video with the outro video
    final_video = concatenate_videoclips([result, video2], method="compose")

    # Write the final concatenated video to a file
    final_video.write_videofile(output_path, codec="libx264", fps=24)

    return output_path


def add_clips_between_videos(main_video, clip_paths):
    """
    Adds two video clips between two segments of a main video.

    Args:
        main_video_path (str): Path to the main video file.
        clip1_path (str): Path to the first video clip to be inserted.
        clip2_path (str): Path to the second video clip to be inserted.
        insert_time (float): Time (in seconds) to insert the clips in the main video.
        output_path (str): Path to save the output video file.

    Returns:
        None
    """

    # Get the video dimensions
    width, height = main_video.size

    # Desired aspect ratio for reels/shorts
    target_aspect_ratio = 9 / 16

    # Calculate the aspect ratio of the input video
    aspect_ratio = width / height

    if aspect_ratio > target_aspect_ratio:
        # Video is wider than the target aspect ratio
        new_width = int(height * target_aspect_ratio)
        x1 = (width - new_width) // 2
        x2 = x1 + new_width
        y1 = 0
        y2 = height
    else:
        # Video is taller than the target aspect ratio
        new_height = int(width / target_aspect_ratio)
        x1 = 0
        x2 = width
        y1 = (height - new_height) // 2
        y2 = y1 + new_height

    # Crop the video to the target aspect ratio
    main_video = crop(main_video, x1=x1, y1=y1, x2=x2, y2=y2)

    video_clips = []
    start_time = 0
    end_time = 5

    for index, clip_path in enumerate(clip_paths):

        clip = VideoFileClip(clip_path)
        clip = clip.without_audio()
        clip = clip.subclip(2, 4)
        clip = clip.set_fps(30)

        # Get the video dimensions
        width, height = clip.size

        # Calculate the aspect ratio of the input video
        aspect_ratio = width / height

        if aspect_ratio > target_aspect_ratio:
            # Video is wider than the target aspect ratio
            new_width = int(height * target_aspect_ratio)
            x1 = (width - new_width) // 2
            x2 = x1 + new_width
            y1 = 0
            y2 = height
        else:
            # Video is taller than the target aspect ratio
            new_height = int(width / target_aspect_ratio)
            x1 = 0
            x2 = width
            y1 = (height - new_height) // 2
            y2 = y1 + new_height

        # Crop the video to the target aspect ratio
        clip = crop(clip, x1=x1, y1=y1, x2=x2, y2=y2)

        clip = clip.resize(main_video.size)

        # clip.write_videofile(f"./output/{start_time}.mp4", threads=2)

        if main_video.duration < end_time:
            segment = main_video.subclip(start_time, main_video.duration)
        else:
            # Extract the segments from the main video
            segment = main_video.subclip(start_time, end_time)

        # Calculate the start and end times based on the clip durations
        start_time = end_time + clip.duration
        end_time = start_time + 5

        video_clips.append(segment)

        video_clips.append(clip)

        clip.close()

        if main_video.duration < start_time:
            break

    if main_video.duration > end_time:
        segment = main_video.subclip(start_time, main_video.duration)
        video_clips.append(segment)

    # final_clip = video_clips[0]
    # for index, video_clip in enumerate(video_clips):
    #     if index == 0:
    #         pass
    #     else:
    #         if index % 2 == 0:
    #             final_clip = fade(final_clip, video_clip, 0.3)
    #         else:
    #             final_clip = add_burn_transition(final_clip, video_clip)

    # Concatenate the video segments and clips
    final_clip = concatenate_videoclips(video_clips)

    # Add the audio
    audio = AudioFileClip("./temp/{video_id}/audio.mp3")

    final_clip = final_clip.set_audio(audio).resize(newsize=(1080, 1920))

    final_clip = final_clip.set_fps(30)

    return final_clip


def get_new_final_video(
    custom_video_path: str,
    subtitles_path: str,
    threads: int,
    subtitles_position: str,
    text_color: str,
    templates: str,
    clip_paths,
):
    # Load the main video and video clips
    main_video = VideoFileClip(custom_video_path)

    video_duration = main_video.duration

    # Required duration of each clip
    req_dur = video_duration / len(clip_paths)

    # Get the size of the video
    width, height = main_video.size

    # Calculate the crop coordinates
    x1 = (width - 500) // 2
    y1 = (height - 500) // 2
    x2 = x1 + 500
    y2 = y1 + 500

    # # Crop the video to a square
    # main_video = main_video.crop(x1=x1, y1=y1, x2=x2, y2=y2).resize((1080, 1080))

    # main_video.write_videofile("./output/template_4.mp4", threads=threads)

    # return

    video_clips = []
    tot_dur = 0

    # Desired aspect ratio for reels/shorts
    target_aspect_ratio = 9 / 16

    for i, clip_path in enumerate(clip_paths):
        clip = VideoFileClip(clip_path)
        clip = clip.without_audio()

        # Check if clip is longer than the remaining audio
        if (video_duration - tot_dur) < clip.duration:
            clip = clip.subclip(2, 2 + (video_duration - tot_dur))
        # Only shorten clips if the calculated clip length (req_dur) is shorter than the actual clip to prevent still image
        elif req_dur < clip.duration:
            clip = clip.subclip(2, 2 + req_dur)

        clip = clip.set_fps(30)

        # Get the video dimensions
        width, height = clip.size

        # Calculate the aspect ratio of the input video
        aspect_ratio = width / height

        if aspect_ratio > target_aspect_ratio:
            # Video is wider than the target aspect ratio
            new_width = int(height * target_aspect_ratio)
            x1 = (width - new_width) // 2
            x2 = x1 + new_width
            y1 = 0
            y2 = height
        else:
            # Video is taller than the target aspect ratio
            new_height = int(width / target_aspect_ratio)
            x1 = 0
            x2 = width
            y1 = (height - new_height) // 2
            y2 = y1 + new_height

        # Crop the video to the target aspect ratio
        clip = crop(clip, x1=x1, y1=y1, x2=x2, y2=y2)

        clip = clip.resize((1080, 1920))

        tot_dur += clip.duration

        # If not the last video, add a transition
        if i < len(clip_paths) - 1 and i >= 1:
            # Get the next video
            current_clip = video_clips[len(video_clips) - 1]
            # Perform the transition
            if i % 2 == 0:
                transition = cross_dissolve(current_clip, clip, 1)
            else:
                transition = slide(current_clip, clip, 1)
            # Add the transition to the list
            video_clips.append(transition)

        video_clips.append(clip)

        clip.close()

    # Concatenate the video segments and clips
    final_clip = concatenate_videoclips(video_clips)

    final_clip = final_clip.set_duration(main_video.duration)

    # 3. Define the Scaling Function for Text Resizing
    def resize(t):
        if t == 5:
            return 20
        # Define starting and ending scale factors
        # Compute the scaling factor linearly over the clip's duration
        scale_factor = 80 - ((30 + t * 5) / 30)
        if scale_factor < 20:
            return 20
        return scale_factor

    # 4. Define the Positioning Function to Center the Text
    def translate(t):
        max_time = 5
        if t > 5:
            return (30, 1100)
        y = 600 + (500 * (t / 5))
        return (30, y)

    # Generate the mask image
    mask_image = circle_mask_with_margin(main_video.get_frame(0), 50)

    # # Create a new video with the white outer line
    # fourcc = cv2.VideoWriter_fourcc(*"XVID")
    # fps = main_video.fps
    # size = main_video.size
    # out = cv2.VideoWriter("output.avi", fourcc, fps, size)

    # for t in range(int(main_video.fps * main_video.duration)):
    #     frame = main_video.get_frame(t / main_video.fps)
    #     mask = circle_mask_with_margin(frame, 50)
    #     frame[mask == 255] = (
    #         255,
    #         255,
    #         255,
    #     )  # set the pixels where the mask is white to white
    #     out.write(frame)

    # out.release()

    # Apply the circle mask to the new video
    mask_clip = ImageClip(mask_image, ismask=True)
    main_video = main_video.set_mask(mask_clip)

    # # Generate the mask image
    # mask_image = circle_mask_with_margin(main_video.get_frame(0), 50)

    # # Apply the circle mask to the video
    # mask_clip = ImageClip(mask_image, ismask=True)

    # main_video = main_video.set_mask(mask_clip)

    # Set the position of the cropped video
    main_video = main_video.set_position(translate)

    # Add the audio
    audio = AudioFileClip("./temp/{video_id}/audio.mp3")

    final_clip = final_clip.set_audio(audio).resize(newsize=(1080, 1920))

    # Combine everything
    final_clip = CompositeVideoClip([final_clip, main_video])

    # Define a generator for creating TextClip objects
    generator = lambda txt: TextClip(
        txt=txt.upper(),
        font="./asset/font/poppins-black.ttf",
        fontsize=100,
        color=text_color,
        stroke_color="black",
        stroke_width=5,
    )

    # Extract the subtitles position
    horizontal_subtitles_position, vertical_subtitles_position = (
        subtitles_position.split(",")
    )

    # Create a SubtitlesClip object
    subtitles = SubtitlesClip(subtitles_path, generator)

    # Composite the main video with the subtitles
    result = CompositeVideoClip(
        [
            final_clip,
            subtitles.set_position(
                (horizontal_subtitles_position, vertical_subtitles_position),
                relative=True,
            ),
        ]
    )

    result = result.set_fps(30)

    result.write_videofile("./output/template6.mp4", threads=threads)

    return "./output/template4.mp4"


@cached_operation
def create_background(image_path, duration):
    return (
        ImageClip(image_path, duration=duration)
        .set_position("center")
        .resize((1280, 720))
        .set_fps(24)
    )


@cached_operation
def create_masked_video(video, mask_size):
    mask_image = circle_masks(video.get_frame(0), mask_size, (670, 360))
    mask_clip = ImageClip(mask_image, ismask=True)
    return video.set_mask(mask_clip)


@cached_operation
def create_circle_clip(video, mask_size):
    return ImageClip(
        circle_mask_with_margin(video, mask_size, (670, 360))
    ).set_duration(video.duration)


def create_video_1(video_id, main_video: str, time):

    width, height = main_video.size

    video = main_video.subclip(0, time)

    background_clip = create_background("./asset/data/bg.png", time)

    video = create_masked_video(video, 45)

    # Set the position of the cropped video
    new_video = video.resize((880, 480)).set_position((200, 120))

    # Repeat the image over time
    circle_clip = create_circle_clip(video, 45).set_position((200, 120))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            background_clip,
            circle_clip.resize((880, 480)),
            new_video,
        ]
    )

    intro_video_path = f"./temp/{video_id}/intro_video.mp4"

    if os.path.exists(intro_video_path):

        intro_clip = VideoFileClip(intro_video_path).resize((1280, 720)).set_fps(24)

        intro_audio_path = "./asset/data/intro_audio.mp3"

        audio_clip = AudioFileClip(intro_audio_path)

        # Set the start time of the audio to 2 seconds before the end of the first video
        audio_start_time = time - 2

        # Composite the original audio of the first video with the new audio
        composite_audio = CompositeAudioClip(
            [final_clip.audio, audio_clip.subclip(0, 6).set_start(audio_start_time)]
        )

        final_clip = fade(final_clip, intro_clip, 0.2)

        final_clip.audio = composite_audio

    return final_clip


def video_1(intro_video_path):

    intro_clip = VideoFileClip(intro_video_path).resize((1280, 720)).set_fps(24)

    intro_audio_path = "./asset/data/intro_audio.mp3"

    audio_clip = AudioFileClip(intro_audio_path)

    # Composite the original audio of the first video with the new audio
    composite_audio = CompositeAudioClip([audio_clip.subclip(1, audio_clip.duration)])

    intro_clip.audio = composite_audio

    return intro_clip


def create_video_2(main_video, title, stock_video, start_time, end_time):

    width, height = main_video.size

    video = main_video.subclip(start_time, end_time)

    time = end_time - start_time

    background_clip = create_background("./asset/data/bg.png", time)

    video = create_masked_video(video, 40)

    # Set the position of the cropped video
    new_video = video.resize((880, 480)).set_position((200, 160))

    # Create a text clip with the title text
    title_clip = TextClip(
        title,
        fontsize=600,
        color="white",
        font="./asset/font/poppins-black.ttf",
    )

    # 4. Define the Positioning Function to Center the Text
    def translate(t):
        if t > 3:
            return (350, 120)
        y = 0 + (120 * (t / 3))
        return (350, y)

    # Animate the title clip with a fade-in effect
    title_clip = (
        title_clip.set_position(translate).set_duration(time).fadein(2).fadeout(2)
    )

    # Resize the title clip to 50% of the video width
    title_clip = title_clip.resize(width=background_clip.w // 2)

    # Repeat the image over time
    circle_clip = create_circle_clip(video, 40).set_position((200, 160))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            background_clip,
            circle_clip.resize((880, 480)),
            new_video,
            title_clip,
        ]
    )

    return final_clip


def combine_long_stock_video(clip_paths, video_duration):

    video_clips = []
    tot_dur = 0

    req_dur = video_duration / len(clip_paths)

    for i, clip_path in enumerate(clip_paths):
        clip = VideoFileClip(clip_path)
        clip = clip.without_audio()

        # Check if clip is longer than the remaining audio
        if (video_duration - tot_dur) < clip.duration:
            clip = clip.subclip(2, 2 + (video_duration - tot_dur))
        # Only shorten clips if the calculated clip length (req_dur) is shorter than the actual clip to prevent still image
        elif req_dur < clip.duration:
            clip = clip.subclip(2, 2 + req_dur)

        clip = clip.set_fps(30)

        width = 1280
        height = 720

        # Get the video dimensions
        video_width, video_height = clip.size

        # Calculate the crop dimensions
        if width > video_width or height > video_height:
            print("Error: Desired dimensions are larger than the input video.")
            return

        x = (video_width - width) // 2
        y = (video_height - height) // 2

        # Crop the video
        clip = clip.crop(x1=x, y1=y, x2=x + width, y2=y + height)

        clip = clip.resize((1280, 720))

        tot_dur += clip.duration

        # If not the last video, add a transition
        if i < len(clip_paths) - 1 and i >= 1:
            # Get the next video
            current_clip = video_clips[len(video_clips) - 1]
            # Perform the transition
            # if i % 2 == 0:
            #     transition = cross_dissolve(current_clip, clip, 1.5)
            # else:
            # transition = fade(current_clip, clip, 1)

            # # Add the transition to the list
            # video_clips.append(transition)

        video_clips.append(clip)

        clip.close()

    # Concatenate the video segments and clips
    final_clip = concatenate_videoclips(video_clips)

    final_clip = final_clip.set_duration(video_duration)

    return final_clip


def create_video_3(main_video, stock_video, subtitles_path, start_time, end_time):

    main_video.duration

    width, height = main_video.size

    video = main_video.subclip(start_time, end_time)

    time = end_time - start_time

    background_image_path = "./asset/data/bg.png"

    background_clip = ImageClip(background_image_path, duration=time).set_position(
        "center"
    )

    # Generate the mask image
    mask_image = circle_masks(video.get_frame(0), 56)

    # Apply the circle mask to the video
    mask_clip = ImageClip(mask_image, ismask=True)

    video = video.set_mask(mask_clip)

    # Set the position of the cropped video
    video = video.set_position((800, 0))

    logo_path = "./asset/data/logo.png"

    # Load the logo
    logo = ImageClip(logo_path, duration=time)

    logo = logo.resize(width=logo.w // 4, height=logo.h // 4)

    # Set the logo position to top right corner
    logo_pos = (background_clip.w - logo.w, 0)

    # Define a generator for creating TextClip objects
    generator = lambda txt: TextClip(
        txt=txt.upper(),
        font="./asset/font/Satoshi-Regular.otf",
        fontsize=100,
        color="#FFFFFF",
        stroke_color="White",
        stroke_width=2,
    )

    # Create a SubtitlesClip object
    subtitles = (
        SubtitlesClip(subtitles_path, generator)
        .subclip(start_time, end_time)
        .set_position((100, 400))
    )

    # Create a single image with the circle
    img = circle_mask_with_margin(video, 57)

    # Create a clip from the image
    circle_clip = ImageClip(img)

    # Repeat the image over time
    circle_clip = circle_clip.set_duration(video.duration).set_position((800, 0))

    # Combine everything
    final_clip = CompositeVideoClip(
        [background_clip, logo.set_position(logo_pos), circle_clip, video, subtitles]
    )

    # stock_subclip = stock_video.subclip(end_time, end_time + 5).resize((1920, 1080))
    # final_clip = fade(final_clip, stock_subclip, 1)

    return final_clip


def get_safe_clip_duration(video, start_time, end_time):
    """
    Get safe clip duration that doesn't exceed video duration
    """
    video_duration = video.duration
    safe_start = min(max(0, start_time), video_duration)
    safe_end = min(end_time, video_duration)

    if safe_start > safe_end:
        return None

    if safe_end == safe_start:
        return safe_start - 1, safe_end

    return (safe_start, safe_end)


def curve_edge(clip, curve_amount):
    """
    Curve the edge of a video.

    Args:
        video_path (str): Path to the input video file.
        curve_amount (float): Amount of curvature (0.0 to 1.0).

    Returns:
        moviepy.editor.VideoClip: The curved video clip.
    """

    # Define the curve function
    def curve(x, y, amount, w, h):
        return x + amount * (x - w / 2) ** 2 / (w**2), y

    # Apply the curve transformation to each frame
    def curve_frame(t):
        frame = clip.get_frame(t)
        curved_frame = np.zeros_like(frame)
        for y in range(frame.shape[0]):
            for x in range(frame.shape[1]):
                x_curved, y_curved = curve(x, y, curve_amount, clip.w, clip.h)
                x_curved = int(x_curved)
                y_curved = int(y_curved)
                if 0 <= x_curved < frame.shape[1] and 0 <= y_curved < frame.shape[0]:
                    curved_frame[y_curved, x_curved] = frame[y, x]
        return curved_frame

    # Create a new clip with the curved frames
    curved_clip = VideoClip(lambda t: curve_frame(t), duration=clip.duration)

    return curved_clip


def create_video_4(main_video, stock_video, start_time, end_time):

    width, height = main_video.size

    video = main_video.subclip(start_time, end_time)

    time = end_time - start_time

    background_image_path = "./asset/data/bg.png"

    background_clip = ImageClip(background_image_path, duration=time).set_position(
        "center"
    )

    # Generate the mask image
    mask_image = circle_masks(video.get_frame(0), 45)

    # Apply the circle mask to the video
    mask_clip = ImageClip(mask_image, ismask=True)

    video = video.set_mask(mask_clip)

    # # Add a margin around the circular region
    # video = video.fx(margin, 8, (165, 42, 42))

    # Set the position of the cropped video
    video = video.set_position((1050, 280))

    logo_path = "./asset/data/logo.png"

    # Load the logo
    logo = ImageClip(logo_path, duration=time)

    logo = logo.resize(width=logo.w // 4, height=logo.h // 4)

    # Set the logo position to top right corner
    logo_pos = (background_clip.w - logo.w, 0)

    stock_subclip = stock_video.subclip(start_time, end_time).resize((1450, 850))

    # stock_subclip = curve_edge(stock_subclip, 0.5)

    # Set the position of the cropped video
    stock_subclip = stock_subclip.set_position((80, 100)).fx(
        vfx.margin, 12, (165, 42, 42)
    )

    # Apply a mask (circular for video2, square for video1 is by default)
    stock_subclip_mask = stock_subclip.add_mask()

    # Create a single image with the circle
    img = circle_mask_with_margin(video, 46)

    # Create a clip from the image
    circle_clip = ImageClip(img)

    # Repeat the image over time
    circle_clip = circle_clip.set_duration(video.duration).set_position((1050, 280))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            background_clip,
            logo.set_position(logo_pos),
            stock_subclip_mask,
            circle_clip,
            video,
        ]
    )

    return final_clip


def create_video_5(main_video, stock_video, start_time, end_time):

    main_video.duration

    width, height = main_video.size

    video = main_video.subclip(start_time, end_time)

    time = end_time - start_time

    # Generate the mask image
    mask_image = circle_masks(video.get_frame(0), 40)

    # Apply the circle mask to the video
    mask_clip = ImageClip(mask_image, ismask=True)

    video = video.set_mask(mask_clip)

    # Set the position of the cropped video
    video = video.set_position((1070, 300))

    stock_subclip = stock_video.subclip(start_time, end_time).resize((1920, 1080))

    logo_path = "./asset/data/logo.png"

    # Load the logo
    logo = ImageClip(logo_path, duration=time)

    logo = logo.resize(width=logo.w // 4, height=logo.h // 4)

    # Set the logo position to top right corner
    logo_pos = (stock_subclip.w - logo.w, 0)

    # Create a single image with the circle
    img = circle_mask_with_margin(video, 41)

    # Create a clip from the image
    circle_clip = ImageClip(img)

    # Repeat the image over time
    circle_clip = circle_clip.set_duration(video.duration).set_position((1070, 300))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            stock_subclip,
            logo.set_position(logo_pos),
            circle_clip,
            video,
        ]
    )

    return final_clip


def create_video_6(video_id, main_video: str, start_time):

    final_clip = main_video.subclip(start_time, main_video.duration)

    outro_video_path = f"./temp/{video_id}/outro_video.mp4"

    if os.path.exists(outro_video_path):

        outro_audio_path = "./asset/data/intro_audio.mp3"

        audio_clip = AudioFileClip(outro_audio_path)

        outro_clip = VideoFileClip(outro_video_path).resize((1280, 720)).set_fps(24)

        outro_clip.audio = audio_clip.subclip(0, audio_clip.duration)

        final_clip = fade(final_clip, outro_clip, 0.3)

    return final_clip


def create_long_video(
    custom_video_path: str,
    subtitles_path: str,
    threads: int,
    subtitles_position: str,
    text_color: str,
    templates: str,
    clip_paths,
):
    # Load the main video and video clips
    main_video = VideoFileClip(custom_video_path)

    video1 = create_video_1(main_video, 5.2)

    stock_video = combine_long_stock_video(clip_paths, main_video.duration)

    video2 = create_video_2(main_video, stock_video, 5.1, 22)

    final_clip = add_burn_transition(video1, video2)

    video3 = create_video_3(main_video, stock_video, subtitles_path, 27, 42)

    final_clip = add_burn_transition(final_clip, video3)

    video4 = create_video_4(main_video, stock_video, 42, 62)

    final_clip = add_burn_transition(final_clip, video4)

    video3 = create_video_3(main_video, stock_video, subtitles_path, 62, 75)

    final_clip = add_burn_transition(final_clip, video3)

    video4 = create_video_4(main_video, stock_video, 75, 90)

    final_clip = add_zoom_transition(final_clip, video4)

    video5 = create_video_5(main_video, stock_video, 90, 110)

    final_clip = add_effect_transition(final_clip, video5)

    video6 = create_video_6(main_video, 110)

    final_clip = add_burn_transition(final_clip, video6)

    final_clip.write_videofile("./output/output1.mp4", threads=5)

    return "./output/output1.mp4"


def create_video_3_copy(main_video, clip, start_time, end_time):

    width, height = main_video.size

    video = main_video.subclip(start_time, end_time)

    time = end_time - start_time

    background_clip = create_background("./asset/data/bg.png", time)

    video = create_masked_video(video, 38)

    new_video = video.resize((880, 480)).set_position((600, 120))

    # Repeat the image over time
    circle_clip = create_circle_clip(video, 38).set_position((600, 120))

    # Generate the mask image
    mask_image = create_rounded_rectangle_mask(clip.get_frame(0), clip.size, 60)

    # Apply the circle mask to the video
    mask_clip = ImageClip(mask_image, ismask=True)

    # Apply a mask (circular for video2, square for video1 is by default)
    clip = clip.set_mask(mask_clip)

    clip = clip.set_position((40, 80))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            background_clip,
            circle_clip.resize((880, 480)),
            new_video,
            clip,
        ]
    )

    return final_clip


def create_video_4_copy(main_video, stock_video, start_time, end_time, end_clip):

    width, height = main_video.size

    video = main_video.subclip(start_time, end_time)

    time = end_time - start_time

    background_clip = create_background("./asset/data/bg.png", time)

    video = create_masked_video(video, 32)

    # Set the position of the cropped video
    new_video = video.resize((780, 420)).set_position((650, 320))

    stock_subclip = stock_video.subclip(0, end_clip).resize((1000, 580))

    # Generate the mask image
    mask_image = create_rounded_rectangle_mask(
        stock_subclip.get_frame(0), stock_subclip.size, 65
    )

    # Apply the circle mask to the video
    mask_clip = ImageClip(mask_image, ismask=True)

    # Apply a mask (circular for video2, square for video1 is by default)
    stock_subclip_mask = stock_subclip.set_mask(mask_clip)

    # Set the position of the cropped video
    stock_subclip = stock_subclip_mask.set_position((40, 70))

    # Repeat the image over time
    circle_clip = create_circle_clip(video, 32).set_position((650, 320))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            background_clip,
            stock_subclip,
            circle_clip.resize((780, 420)),
            new_video,
        ]
    )

    return final_clip


def video_4_copy(stock_video):

    background_clip = create_background("./asset/data/bg.png", stock_video.duration)

    stock_subclip = stock_video.resize((1000, 550)).set_fps(24)

    # Generate the mask image
    mask_image = create_rounded_rectangle_mask(
        stock_subclip.get_frame(0), stock_subclip.size, 65
    )

    # Apply the circle mask to the video
    mask_clip = ImageClip(mask_image, ismask=True)

    # Apply a mask (circular for video2, square for video1 is by default)
    stock_subclip_mask = stock_subclip.set_mask(mask_clip)

    # Set the position of the cropped video
    stock_subclip = stock_subclip_mask.set_position((130, 70))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            background_clip,
            stock_subclip,
        ]
    )

    return final_clip


def create_video_5_copy(main_video, stock_video, start_time, end_time, end_clip):

    width, height = main_video.size

    video = main_video.subclip(start_time, end_time)

    video = create_masked_video(video, 32)

    # Set the position of the cropped video
    new_video = video.resize((780, 420)).set_position((650, 320))

    stock_subclip = stock_video.subclip(0, end_clip)

    # Repeat the image over time
    circle_clip = create_circle_clip(video, 32).set_position((650, 320))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            stock_subclip,
            circle_clip.resize((780, 420)),
            new_video,
        ]
    )

    return final_clip


def video_5_copy(stock_video):

    stock_subclip = stock_video.resize((1280, 720)).set_fps(24)

    return stock_subclip


def create_video_6_copy(main_video: str, start_time, end_time):

    width, height = main_video.size

    time = end_time - start_time

    video = main_video.subclip(start_time, end_time)

    background_clip = create_background("./asset/data/bg.png", time)

    video = create_masked_video(video, 45)

    # Set the position of the cropped video
    new_video = video.resize((880, 480)).set_position((200, 120))

    # Repeat the image over time
    circle_clip = create_circle_clip(video, 45).set_position((200, 120))

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            background_clip,
            circle_clip.resize((880, 480)),
            new_video,
        ]
    )

    return final_clip


def test_long_video(
    video_id,
    user_id: str,
    custom_videos,
    title: str,
    clips,
    stock_video_clips,
    images,
    video_file_path,
    intro_time=8,
    logo=None,
):

    if video_file_path:
        event_video = VideoFileClip(video_file_path)

    main_video = []
    for video_path in custom_videos:
        main_video.append(VideoFileClip(video_path))

    # Load the main video and video clips
    main_video = concatenate_videoclips(main_video).resize((1280, 720)).set_fps(24)

    final_clip = create_video_1(video_id, main_video, intro_time)

    end_clip_time = 0
    image_at_time = 0

    if clips:

        for index, clip in enumerate(clips):

            clip_duration = clip["clip_duration"]
            at_time = int(clip["atTime"])

            if at_time > main_video.duration:
                break

            if index < len(clips) - 1:
                next_at_time = int(clips[index + 1]["atTime"])
            else:
                next_at_time = main_video.duration - 5

            if next_at_time > main_video.duration:
                next_at_time = main_video.duration - 5

            if index < len(images):
                image = int(images[index]["image"])
                image_at_time = int(images[index]["atTime"])

            if index == 0:
                clip = create_video_2(
                    main_video, title, final_clip, intro_time, intro_time + 5
                )
                final_clip = add_burn_transition(final_clip, clip)
                end_clip_time = intro_time + 5

            if end_clip_time < at_time:

                if image_at_time < at_time and index % 2 == 0:
                    image_path = f"./temp/{video_id}/image_{image}.jpg"
                    clip = ImageClip(
                        image_path, duration=(at_time - end_clip_time)
                    ).resize((780, 560))
                    video3 = create_video_3_copy(
                        main_video, clip, end_clip_time, at_time
                    )
                else:
                    video3 = create_video_6_copy(main_video, end_clip_time, at_time)

                final_clip = add_animation_transition(final_clip, video3)

                end_clip_time = at_time

            if end_clip_time <= at_time or end_clip_time < next_at_time:

                clip_duration = get_safe_clip_duration(event_video, *clip_duration)

                clip = event_video.subclip(*clip_duration)

                end_time = 0

                clip = clip.set_audio(None).resize((1280, 720)).set_fps(24)

                start_time = at_time if at_time >= end_clip_time else end_clip_time

                if (start_time + clip.duration) > next_at_time:
                    end_time = next_at_time
                else:
                    end_time = start_time + clip.duration

                if index % 2 == 0:

                    video4 = create_video_4_copy(
                        main_video,
                        clip,
                        start_time,
                        end_time,
                        end_time - start_time,
                    )
                    final_clip = add_burn_transition(final_clip, video4)

                else:

                    video5 = create_video_5_copy(
                        main_video,
                        clip,
                        start_time,
                        end_time,
                        end_time - start_time,
                    )

                    final_clip = add_animation_transition(final_clip, video5)

                end_clip_time = end_time

    else:

        # Create a defaultdict to store the merged data, sorted by 'at_time'
        merged_data = defaultdict(list)

        # Add data1 items to the merged_data dictionary
        for item in images:
            merged_data[item["atTime"]].append({"image": item["image"]})

        # Add data2 items to the merged_data dictionary
        for item in stock_video_clips:
            merged_data[item["at_time"]].append({"search_terms": item["search_terms"]})

        # Sort the keys (at_time values) in increasing order
        sorted_keys = sorted(merged_data.keys())

        merged_json = [
            {"at_time": k, **{key: value for d in v for key, value in d.items()}}
            for k, v in zip(sorted_keys, [merged_data[key] for key in sorted_keys])
        ]

        print("merged_json", merged_json)

        clip_num_stock = 0

        for index, data in enumerate(merged_json):
            if "image" in data:
                image = data["image"]
                last_image_path = f"./temp/{video_id}/image_{image}.jpg"
                break

        for index, data in enumerate(merged_json):

            at_time = int(data["at_time"])

            if at_time > main_video.duration:
                break

            if index < len(merged_json) - 1:
                next_at_time = int(merged_json[index + 1]["at_time"])
            else:
                next_at_time = main_video.duration - 3
            if next_at_time > main_video.duration:
                next_at_time = main_video.duration - 3

            if index == 0:
                clip = create_video_2(
                    main_video, title, final_clip, intro_time, intro_time + 5
                )
                final_clip = add_burn_transition(final_clip, clip)
                end_clip_time = intro_time + 5

            if end_clip_time < at_time:

                if index % 2 == 0:
                    clip = ImageClip(
                        last_image_path, duration=(at_time - end_clip_time)
                    ).resize((780, 560))
                    video3 = create_video_3_copy(
                        main_video, clip, end_clip_time, at_time
                    )
                else:
                    video3 = create_video_6_copy(main_video, end_clip_time, at_time)

                final_clip = add_animation_transition(final_clip, video3)

                end_clip_time = at_time

            if end_clip_time <= at_time or end_clip_time < next_at_time:

                if "search_terms" in data:
                    clip = VideoFileClip(f"./temp/{video_id}/{clip_num_stock}.mp4")
                    clip = clip.set_audio(None).resize((1280, 720)).set_fps(24)
                    start_time = at_time if at_time >= end_clip_time else end_clip_time
                    if (start_time + clip.duration) > next_at_time:
                        end_time = next_at_time
                    else:
                        end_time = start_time + clip.duration
                else:
                    image = data["image"]
                    image_path = f"./temp/{video_id}/image_{image}.jpg"
                    duration = next_at_time - end_clip_time
                    if duration > 0:
                        clip = (
                            ImageClip(image_path, duration=duration)
                            .resize((1280, 720))
                            .set_fps(24)
                        )
                        last_image_path = image_path
                        start_time = end_clip_time
                        end_time = next_at_time
                    continue

                if index % 2 == 0:
                    video4 = create_video_4_copy(
                        main_video,
                        clip,
                        start_time,
                        end_time,
                        end_time - start_time,
                    )
                    final_clip = add_burn_transition(final_clip, video4)
                else:
                    video5 = create_video_5_copy(
                        main_video,
                        clip,
                        start_time,
                        end_time,
                        end_time - start_time,
                    )
                    final_clip = add_animation_transition(final_clip, video5)
                end_clip_time = end_time
            if "search_terms" in data:
                clip_num_stock = clip_num_stock + 1

    if end_clip_time < main_video.duration:
        video6 = create_video_6(video_id, main_video, end_clip_time)
        final_clip = add_burn_transition(final_clip, video6)

    logo_path = f"./temp/{video_id}/logo.png"

    if not os.path.exists(logo_path):
        logo_path = "./asset/data/ciny_logo.png"

    position = logo.get("position", "top-right")
    size = logo.get("size", "medium")

    logo, logo_pos = create_logo(
        final_clip,
        logo_path,
        position=position,
        size=size,
    )

    final_clip = CompositeVideoClip([final_clip, logo.set_position(logo_pos)])

    final_clip = final_clip.resize((1280, 720)).set_fps(24)

    final_clip.write_videofile(
        f"./temp/{video_id}/{video_id}.mp4",
        threads=multiprocessing.cpu_count(),
        codec="libx264",
        preset="fast",  # Faster encoding, larger file size
        ffmpeg_params=["-loglevel", "error", "-tune", "fastdecode"],
        logger=ProgressLogger(video_id, user_id),
    )

    duration = final_clip.duration

    final_clip.close()

    return f"./temp/{video_id}/{video_id}.mp4", duration


def long_video1(
    video_id: str,
    user_id: str,
    audio_path: str,
    clips,
    images,
    video_data,
    video_file_path,
    logo,
):

    if video_file_path:
        event_video = VideoFileClip(video_file_path)

    video_functions = [video_4_copy, video_5_copy]

    transition_functions = [
        add_animation_transition,
        add_burn_transition,
        add_zoom_in_transition,
        add_zoom_out_transition,
    ]

    # Load the main video and video clips
    main_audio = AudioFileClip(audio_path)

    # Create a defaultdict to store the merged data, sorted by 'at_time'
    merged_data = defaultdict(list)

    # Add data1 items to the merged_data dictionary
    for item in images:
        merged_data[item["atTime"]].append({"image": item["image"]})

    if clips:
        # Add data1 items to the merged_data dictionary
        for item in clips:
            merged_data[item["atTime"]].append(
                {"clip": item["clip"], "clip_duration": item["clip_duration"]}
            )

    # Add data2 items to the merged_data dictionary
    for item in video_data:
        merged_data[item["at_time"]].append({"search_terms": item["search_terms"]})

    # Sort the keys (at_time values) in increasing order
    sorted_keys = sorted(merged_data.keys())

    merged_json = [
        {"at_time": k, **{key: value for d in v for key, value in d.items()}}
        for k, v in zip(sorted_keys, [merged_data[key] for key in sorted_keys])
    ]

    print("merged_json", merged_json)

    clip_num_stock = 0

    for index, data in enumerate(merged_json):
        if "image" in data:
            image = data["image"]
            last_image_path = f"./temp/{video_id}/image_{image}.jpg"
            break

    intro_path = f"./temp/{video_id}/intro_video.mp4"

    endtime = 0
    final_clip = None
    if os.path.exists(intro_path):
        final_clip = video_1(intro_path)
        endtime = final_clip.duration

    for index, data in enumerate(merged_json):

        at_time = int(data["at_time"])

        if at_time > main_audio.duration:
            break

        if index < len(merged_json) - 1:
            next_at_time = int(merged_json[index + 1]["at_time"])
            is_next_video_clip = "clip" in merged_json[index + 1]
        else:
            next_at_time = main_audio.duration

        if next_at_time > main_audio.duration:
            next_at_time = main_audio.duration

        if endtime < at_time and endtime != 0:

            clip = ImageClip(last_image_path, duration=(at_time - endtime))

            audio = main_audio.subclip(endtime, at_time)

            clip = clip.set_audio(audio)

            video = video_4_copy(
                clip,
            )

            final_clip = add_burn_transition(final_clip, video)

            endtime = at_time

        if endtime <= at_time or endtime < next_at_time:

            if "search_terms" in data:
                clip = VideoFileClip(f"./temp/{video_id}/{clip_num_stock}.mp4")
                end = (
                    next_at_time
                    if next_at_time < endtime + clip.duration
                    else endtime + clip.duration
                )

                audio = main_audio.subclip(endtime, end)
                clip = clip.subclip(0, end - endtime)
                endtime = end

            elif "clip" in data:
                clip_duration = data["clip_duration"]
                clip_duration = get_safe_clip_duration(event_video, *clip_duration)
                clip = event_video.subclip(*clip_duration)

                end = (
                    next_at_time
                    if next_at_time < endtime + clip.duration and is_next_video_clip
                    else endtime + clip.duration
                )
                if end > main_audio.duration:
                    end = main_audio.duration
                audio = main_audio.subclip(endtime, endtime + clip.duration)

                clip = clip.subclip(0, end - endtime)
                endtime = end

            else:
                image = data["image"]
                image_path = f"./temp/{video_id}/image_{image}.jpg"
                duration = next_at_time - endtime
                audio = main_audio.subclip(endtime, next_at_time)
                clip = ImageClip(image_path, duration=duration)
                last_image_path = image_path
                endtime = next_at_time

            clip = clip.set_audio(audio)

            # Randomly select a function
            selected_function = random.choice(video_functions)
            # Use the selected function
            video = selected_function(clip)
            if final_clip:
                selected_function = random.choice(transition_functions)
                final_clip = selected_function(final_clip, video)
            else:
                final_clip = video

        if "search_terms" in data:
            clip_num_stock = clip_num_stock + 1

    final_clip = create_video_6(video_id, final_clip, 0)

    logo_path = f"./temp/{video_id}/logo.png"

    if not os.path.exists(logo_path):
        logo_path = "./asset/data/ciny_logo.png"

    position = logo.get("position", "top-right")
    size = logo.get("size", "medium")

    logo, logo_pos = create_logo(
        final_clip,
        logo_path,
        position=position,
        size=size,
    )

    final_clip = CompositeVideoClip([final_clip, logo.set_position(logo_pos)])

    final_clip = final_clip.resize((1280, 720)).set_fps(24)

    final_clip.write_videofile(
        f"./temp/{video_id}/{video_id}.mp4",
        threads=multiprocessing.cpu_count(),
        codec="libx264",
        preset="fast",  # Faster encoding, larger file size
        ffmpeg_params=["-loglevel", "error", "-tune", "fastdecode"],
        logger=ProgressLogger(video_id, user_id),
    )

    duration = final_clip.duration

    final_clip.close()

    return f"./temp/{video_id}/{video_id}.mp4", duration


def test_clip(title, stock_video):

    # Create a text clip with the title text
    title_clip = TextClip(
        title,
        fontsize=50,
        color="white",
        font="./asset/font/poppins-black.ttf",
    )

    # Animate the title clip with a fade-in effect
    title_clip = title_clip.set_position(("center", "center")).set_duration(5)

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            stock_video.resize((1280, 720)).set_duration(5).set_opacity(0.8),
            title_clip,
        ]
    )

    return final_clip
