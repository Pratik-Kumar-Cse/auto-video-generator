from collections import defaultdict
import random
import numpy as np
from PIL import Image, ImageDraw
import time
from functools import lru_cache
import multiprocessing
import io

from scipy.ndimage import gaussian_filter
from moviepy.video.tools.subtitles import SubtitlesClip
from app.loggers.progress_logger import ProgressLogger
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    clips_array,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)
from ..utils import download_font

from .transition import fade, add_zoom_out_transition, add_zoom_in_transition

from .video_edit import (
    circle_masks,
    circle_mask_with_margin,
    create_rounded_rectangle_mask,
)


from ..music import music_service


import os
import sys
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import ffmpeg


from functools import partial

# Cache for processed clips
clip_cache = {}

transition_functions = [fade, add_zoom_in_transition, add_zoom_out_transition]

# Force UTF-8 encoding
sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
io.DEFAULT_ENCODING = "utf-8"

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Caching function
def cached_operation(func):
    @lru_cache(maxsize=None)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


# def create_reel_video_template(template_func):
#     @cached_operation
#     def wrapper(*args, **kwargs):
#         return template_func(*args, **kwargs)

#     return wrapper


# @create_reel_video_template
# def create_reel_video_1(main_video, clip, start_time, end_time):
#     # Implementation of create_reel_video_1
#     time = end_time - start_time
#     video = create_masked_video(main_video.subclip(start_time, end_time), 45)
#     new_video = video.resize((1280, 720)).set_position((-120, 1150))

#     background_clip = ImageClip(
#         "./asset/data/background.jpg", duration=time
#     ).set_position("center")
#     logo = create_logo("./asset/data/logo1.png", time)
#     circle_clip = (
#         ImageClip(circle_mask_with_margin(video, 46))
#         .set_duration(video.duration)
#         .set_position((-120, 1150))
#     )

#     if clip:
#         video_clip_mask = clip.add_mask()
#         return CompositeVideoClip(
#             [create_base_clip(background_clip, logo, circle_clip, new_video), clip]
#         )
#     else:
#         return create_base_clip(background_clip, logo, circle_clip, video)


# @create_reel_video_template
# def create_reel_video_2(main_video, clip, start_time, end_time):
#     pass
#     # Implementation of create_reel_video_2
#     # ... (fill in with the actual implementation)


# def create_reel_video2(
#     video_id,
#     custom_video_path,
#     subtitles_path,
#     clips,
#     images,
#     template_id,
#     is_event_video=True,
# ):
#     if not is_event_video:
#         return

#     main_video = VideoFileClip(custom_video_path)

#     # Prepare all clips in parallel
#     with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
#         futures = [
#             executor.submit(
#                 process_clip, main_video, clip, images, subtitles_path, template_id, i
#             )
#             for i, clip in enumerate(clips)
#         ]
#         processed_clips = [future.result() for future in as_completed(futures)]

#     # Concatenate all processed clips
#     final_clip = concatenate_videoclips(processed_clips)

#     final_clip = final_clip.resize((720, 1280)).set_fps(24)
#     final_clip.write_videofile(f"./temp/{video_id}.mp4", threads=os.cpu_count())
#     return f"./temp/{video_id}.mp4"


# def get_video_info(file_path):
#     probe = ffmpeg.probe(file_path)
#     video_info = next(s for s in probe["streams"] if s["codec_type"] == "video")
#     return {
#         "width": int(video_info["width"]),
#         "height": int(video_info["height"]),
#         "duration": float(video_info["duration"]),
#     }


# def create_circle_mask(size, output_path):
#     ffmpeg.input(f"color=white:s={size}x{size}", f="lavfi", duration=1).filter(
#         "geq",
#         "lum=255*(1-4*((X-(W/2))^2+(Y-(H/2))^2)/(W^2)):a=255*(1-4*((X-(W/2))^2+(Y-(H/2))^2)/(W^2))",
#     ).output(output_path, vframes=1).overwrite_output().run(
#         capture_stdout=True, capture_stderr=True
#     )


# def create_text_overlay(text, font_file, font_size, output_path):
#     ffmpeg.input(f"color=transparent:s=1080x1920", f="lavfi", duration=1).drawtext(
#         text=text,
#         fontfile=font_file,
#         fontsize=font_size,
#         fontcolor="white",
#         x="(w-text_w)/2",
#         y="(h-text_h)/2",
#         borderw=2,
#         bordercolor="white",
#     ).output(output_path, vframes=1).overwrite_output().run(
#         capture_stdout=True, capture_stderr=True
#     )


# def process_clip(
#     main_video, clip_data, images, subtitles, template_id, index, temp_dir
# ):
#     clip_num = int(clip_data["clip"])
#     at_time = int(clip_data["atTime"])

#     clip_path = f"{temp_dir}/clip_{clip_num - 1}.mp4"
#     output_path = f"{temp_dir}/processed_clip_{index}.mp4"

#     main_stream = ffmpeg.input(main_video, ss=at_time, t=6)
#     clip_stream = ffmpeg.input(clip_path)

#     if template_id == "template_1":
#         mask_path = f"{temp_dir}/circle_mask.png"
#         create_circle_mask(720, mask_path)

#         masked_main = main_stream.crop(
#             x="in_w/2 - 360", y="in_h/2 - 360", w=720, h=720
#         ).overlay(ffmpeg.input(mask_path), repeatlast=1)

#         background = ffmpeg.input("./asset/data/background.jpg")

#         output = ffmpeg.filter(
#             [background, masked_main], "overlay", x="W/2-w/2", y="H/2-h/2"
#         )
#     elif template_id == "template_2":
#         output = ffmpeg.filter(
#             [main_stream, clip_stream], "overlay", x="W/2-w/2", y="H-h"
#         )
#     else:
#         # Add more templates as needed
#         output = main_stream

#     if index < len(subtitles):
#         subtitle_text = subtitles[index]["text"]
#         subtitle_overlay_path = f"{temp_dir}/subtitle_{index}.png"
#         create_text_overlay(
#             subtitle_text,
#             "./asset/font/Satoshi-Regular.otf",
#             80,
#             subtitle_overlay_path,
#         )
#         output = ffmpeg.filter([output, ffmpeg.input(subtitle_overlay_path)], "overlay")

#     output.output(output_path, t=6).overwrite_output().run(
#         capture_stdout=True, capture_stderr=True
#     )

#     return output_path


# def create_reel_video1(
#     video_id,
#     custom_video_path,
#     subtitles_path,
#     clips,
#     images,
#     template_id,
# ):

#     temp_dir = f"./temp/{video_id}"

#     with open(subtitles_path, "r") as f:
#         subtitles = json.load(f)

#     with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
#         futures = [
#             executor.submit(
#                 process_clip,
#                 custom_video_path,
#                 clip,
#                 images,
#                 subtitles,
#                 template_id,
#                 i,
#                 temp_dir,
#             )
#             for i, clip in enumerate(clips)
#         ]
#         processed_clips = [future.result() for future in as_completed(futures)]

#     # Concatenate all processed clips
#     concat_list_path = f"{temp_dir}/concat_list.txt"
#     with open(concat_list_path, "w") as f:
#         for clip_path in processed_clips:
#             f.write(f"file '{clip_path}'\n")

#     output_path = f"./temp/{video_id}.mp4"

#     ffmpeg.input(concat_list_path, f="concat", safe=0).output(
#         output_path, vf="scale=720:1280", r=24
#     ).overwrite_output().run(capture_stdout=True, capture_stderr=True)

#     # Clean up temporary files
#     for clip_path in processed_clips:
#         os.remove(clip_path)
#     os.remove(concat_list_path)

#     return output_path


# def create_base_clip(background_clip, logo, circle_clip, video):
#     return CompositeVideoClip(
#         [
#             background_clip,
#             logo.set_position((background_clip.w - logo.w - 30, 40)),
#             circle_clip.resize((1280, 720)),
#             video,
#         ]
#     )


@cached_operation
def create_masked_video(video, mask_size):
    mask_image = circle_masks(video.get_frame(0), mask_size, (670, 360))
    mask_clip = ImageClip(mask_image, ismask=True)
    return video.set_mask(mask_clip)


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
        "small": 0.03,  # 3% of video height
        "medium": 0.04,  # 4% of video height
        "large": 0.05,  # 5% of video height
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


@cached_operation
def create_background(template_id, duration):
    background_images = {
        "template_1": "background.jpg",
        "template_2": "background.jpg",
        "template_3": "background_2.jpg",
        "template_4": "background_1.jpg",
    }
    background = background_images.get(template_id, "background.jpg")
    image_path = f"./asset/data/{background}"
    return (
        ImageClip(image_path, duration=duration)
        .set_position("center")
        .resize((720, 1280))
    )


@cached_operation
def create_circle_clip(video, mask_size):
    return ImageClip(
        circle_mask_with_margin(video, mask_size, (670, 360))
    ).set_duration(video.duration)


@cached_operation
def create_text_generator(
    font_path="./asset/font/bold_font.ttf", font_size=50, color="#FFFF00"
):

    if font_path != "./asset/font/bold_font.ttf":
        font_path = download_font(font_path)
    return lambda txt: TextClip(
        txt=txt.upper(),
        font=font_path,
        fontsize=font_size,
        color=color,
        stroke_color="Black",
        stroke_width=2,
        align="center",
        method="label",
    )


def reel_video(main_audio, clip, start_time, end_time):

    audio = main_audio.subclip(start_time, end_time)

    # Get the original video dimensions
    original_width, original_height = clip.size

    # Calculate the aspect ratio of the original video
    original_aspect_ratio = original_width / original_height

    # Define the desired aspect ratio for Shorts (9:16)
    shorts_aspect_ratio = 9 / 16

    # Determine if we need to crop horizontally or vertically
    if original_aspect_ratio > shorts_aspect_ratio:
        # Crop horizontally
        new_width = int(original_height * shorts_aspect_ratio)
        new_height = original_height
        x1 = (original_width - new_width) // 2
        x2 = x1 + new_width
        y1 = 0
        y2 = original_height
    else:
        # Crop vertically
        new_height = int(original_width / shorts_aspect_ratio)
        new_width = original_width
        x1 = 0
        x2 = original_width
        y1 = (original_height - new_height) // 2
        y2 = y1 + new_height

    # Crop the video
    clip = clip.crop(x1=x1, x2=x2, y1=y1, y2=y2)

    clip = clip.resize((480, 854))

    final_clip = clip.set_audio(audio)

    return final_clip


def create_reel_video_1(
    main_video, clip, subtitles, start_time, end_time, template_id="template_1"
):

    width, height = main_video.size

    time = end_time - start_time

    video = create_masked_video(main_video.subclip(start_time, end_time), 40)

    new_video = video.resize((1080, 600)).set_position((-180, 700))

    background_clip = create_background(template_id, time)

    circle_clip = (
        create_circle_clip(video, 40).resize((1080, 600)).set_position((-180, 700))
    )

    # Create a SubtitlesClip object
    subtitles = subtitles.subclip(start_time, end_time)

    if clip:

        clip = clip.resize((890, 500))
        # Get the video dimensions
        video_width, video_height = clip.size

        # Calculate the coordinates for cropping
        x1 = (video_width - 600) // 2
        y1 = (video_height - 500) // 2
        x2 = video_width - x1
        y2 = video_height - y1

        clip = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2).resize((600, 500))

        # Generate the mask image
        mask_image = create_rounded_rectangle_mask(clip.get_frame(0), clip.size, 60)

        # Apply the circle mask to the video
        mask_clip = ImageClip(mask_image, ismask=True)

        # Apply a mask (circular for video2, square for video1 is by default)
        clip = clip.set_mask(mask_clip)

        # Combine everything
        final_clip = CompositeVideoClip(
            [
                background_clip,
                circle_clip,
                new_video,
                subtitles.set_position(("center", 640)),
                clip.set_position((60, 100)),
            ]
        )
    else:
        # Combine everything
        final_clip = CompositeVideoClip(
            [
                background_clip,
                subtitles.set_position(("center", 1120)),
                circle_clip.set_position((-180, 300)),
                new_video.set_position((-180, 300)),
            ]
        )

    return final_clip


def create_reel_video_5(main_video, clip, subtitles, start_time, end_time):

    # Get the original video dimensions
    original_width, original_height = clip.size

    # Calculate the aspect ratio of the original video
    original_aspect_ratio = original_width / original_height

    # Define the desired aspect ratio for Shorts (9:16)
    shorts_aspect_ratio = 9 / 16

    # Determine if we need to crop horizontally or vertically
    if original_aspect_ratio > shorts_aspect_ratio:
        # Crop horizontally
        new_width = int(original_height * shorts_aspect_ratio)
        new_height = original_height
        x1 = (original_width - new_width) // 2
        x2 = x1 + new_width
        y1 = 0
        y2 = original_height
    else:
        # Crop vertically
        new_height = int(original_width / shorts_aspect_ratio)
        new_width = original_width
        x1 = 0
        x2 = original_width
        y1 = (original_height - new_height) // 2
        y2 = y1 + new_height

    # Crop the video
    clip = clip.crop(x1=x1, x2=x2, y1=y1, y2=y2)

    clip = clip.resize((720, 1280))

    width, height = main_video.size

    video = create_masked_video(main_video.subclip(start_time, end_time), 32)

    # Set the position of the cropped video
    new_video = video.resize((712, 400)).set_position((-200, 0))

    circle_clip = (
        create_circle_clip(video, 32).resize((712, 400)).set_position((-200, 0))
    )

    # Create a SubtitlesClip object
    subtitles = subtitles.subclip(start_time, end_time)

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            clip,
            circle_clip,
            new_video,
            subtitles.set_position(("center", "center")),
        ]
    )

    return final_clip


def create_reel_video_2(main_video, clip, subtitles, start_time, end_time):

    # Get the original video dimensions
    original_width, original_height = clip.size

    # Calculate the aspect ratio of the original video
    original_aspect_ratio = original_width / original_height

    # Define the desired aspect ratio for Shorts (9:16)
    shorts_aspect_ratio = 9 / 16

    # Determine if we need to crop horizontally or vertically
    if original_aspect_ratio > shorts_aspect_ratio:
        # Crop horizontally
        new_width = int(original_height * shorts_aspect_ratio)
        new_height = original_height
        x1 = (original_width - new_width) // 2
        x2 = x1 + new_width
        y1 = 0
        y2 = original_height
    else:
        # Crop vertically
        new_height = int(original_width / shorts_aspect_ratio)
        new_width = original_width
        x1 = 0
        x2 = original_width
        y1 = (original_height - new_height) // 2
        y2 = y1 + new_height

    # Crop the video
    clip = clip.crop(x1=x1, x2=x2, y1=y1, y2=y2)

    clip = clip.resize((720, 1280))

    width, height = main_video.size

    video = create_masked_video(main_video.subclip(start_time, end_time), 38)

    # Set the position of the cropped video
    new_video = video.resize((1080, 600)).set_position((-180, 700))

    circle_clip = (
        create_circle_clip(video, 38).resize((1080, 600)).set_position((-180, 700))
    )

    # Create a SubtitlesClip object
    subtitles = subtitles.subclip(start_time, end_time)

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            clip,
            circle_clip,
            new_video,
            subtitles.set_position(("center", "center")),
        ]
    )

    return final_clip


def create_reel_video_3(
    main_video, subtitles, start_time, end_time, template_id="template_1"
):

    width, height = main_video.size

    time = end_time - start_time

    background_clip = create_background(template_id, time)

    video = create_masked_video(main_video.subclip(start_time, end_time), 38)

    # Set the position of the cropped video
    new_video = video.resize((1080, 600)).set_position((-180, 400))

    circle_clip = (
        create_circle_clip(video, 38).resize((1080, 600)).set_position((-180, 400))
    )

    # Create a SubtitlesClip object
    subtitles = subtitles.subclip(start_time, end_time)

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            background_clip,
            circle_clip,
            new_video,
            subtitles.set_position(("center", 1150)),
        ]
    )

    return final_clip


def create_reel_video_4(main_video, clip, subtitles, start_time, end_time):

    width, height = main_video.size

    video = main_video.subclip(start_time, end_time)

    video = video.crop(x1=315, y1=20, x2=1025, y2=620).resize(newsize=(720, 600))

    clip = clip.resize((1210, 680))
    # Get the video dimensions
    video_width, video_height = clip.size

    # Calculate the coordinates for cropping
    x1 = (video_width - 720) // 2
    y1 = (video_height - 680) // 2
    x2 = video_width - x1
    y2 = video_height - y1

    clip = clip.crop(x1=x1, y1=y1, x2=x2, y2=y2).resize(newsize=(720, 680))

    # Stack the resized video clips on top of each other
    final_clip = clips_array([[clip], [video]])

    final_clip = final_clip.resize(newsize=(720, 1280))

    # Create a SubtitlesClip object
    subtitles = subtitles.subclip(start_time, end_time)

    # Combine everything
    final_clip = CompositeVideoClip(
        [
            final_clip,
            subtitles.set_position(("center", "center")),
        ]
    )

    return final_clip


def create_reel_video(
    video_id: str,
    user_id: str,
    custom_videos: str,
    subtitles_path: str,
    clips,
    images,
    video_data,
    template_id,
    is_event_video,
    video_file_path,
    caption,
    music_media_id,
    logo,
):

    if video_file_path:
        event_video = VideoFileClip(video_file_path)

    main_video = []
    for video_path in custom_videos:
        main_video.append(VideoFileClip(video_path))
    # Load the main video and video clips
    main_video = concatenate_videoclips(main_video)

    main_video = main_video.resize((1280, 720)).set_fps(24)

    end_clip_time = 0
    final_clip = None
    clip_num = 0

    if caption:
        generator = create_text_generator(
            font_path=caption.get("font_path"),
            font_size=50,
            color=caption.get("color_code"),
        )
    else:
        # Pre-render subtitles
        generator = create_text_generator("./asset/font/bold_font.ttf", 50)

    subtitles = SubtitlesClip(
        subtitles_path,
        generator,
    ).set_duration(main_video.duration)

    if "template_5" == template_id:
        return test_reel_video(
            video_id,
            main_video,
            subtitles,
            clips,
            images,
            event_video,
            logo,
            music_media_id,
            user_id,
        )

    temp_functions = {
        "template_1": create_reel_video_4,
        "template_2": create_reel_video_1,
        "template_3": create_reel_video_2,
        "template_4": create_reel_video_5,
    }

    temp_functions = temp_functions.get(template_id, create_reel_video_4)

    if is_event_video:
        for index, clip in enumerate(clips):
            clip_duration = clip["clip_duration"]
            at_time = int(clip["atTime"])

            if at_time > main_video.duration:
                break

            if index < len(clips) - 1:
                next_at_time = int(clips[index + 1]["atTime"])
            else:
                next_at_time = main_video.duration

            if next_at_time > main_video.duration:
                next_at_time = main_video.duration

            if index < len(images):
                image = int(images[index]["image"])

            if end_clip_time == 0 and at_time != 0:
                end_time = at_time if at_time < 5 else 5

                final_clip = create_reel_video_1(
                    main_video, None, subtitles, 0, end_time, template_id
                )
                end_clip_time = end_time

            if end_clip_time < at_time:

                image_path = f"./temp/{video_id}/image_{image}.jpg"

                clip = ImageClip(image_path, duration=(at_time - end_clip_time))

                clip = clip.resize((1280, 720)).set_fps(24)

                start_time = end_clip_time
                end_time = at_time

                args = [main_video, clip, subtitles, start_time, end_time]

                video = temp_functions(*args)

                if final_clip is not None:

                    final_clip = fade(final_clip, video)

                else:
                    final_clip = video

                end_clip_time = at_time

            clip = event_video.subclip(*clip_duration)

            clip = clip.set_audio(None).resize((1280, 720)).set_fps(24)

            start_time = at_time if at_time >= end_clip_time else end_clip_time

            if (start_time + clip.duration) > next_at_time:
                end_time = next_at_time
            else:
                end_time = start_time + clip.duration

            time = end_time - start_time

            clip = clip.subclip(0, time)
            args = [main_video, clip, subtitles, start_time, end_time]

            video = temp_functions(*args)

            if final_clip is not None:
                # selected_function = random.choice(transition_functions)
                final_clip = fade(final_clip, video, 0)
            else:
                final_clip = video

            end_clip_time = end_time
    else:
        # Create a defaultdict to store the merged data, sorted by 'at_time'
        merged_data = defaultdict(list)

        # Add data1 items to the merged_data dictionary
        for item in images:
            merged_data[item["atTime"]].append({"image": item["image"]})

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

        for index, data in enumerate(merged_json):

            at_time = int(data["at_time"])

            if at_time > main_video.duration:
                break

            if index < len(merged_json) - 1:
                next_at_time = int(merged_json[index + 1]["at_time"])
            else:
                next_at_time = main_video.duration

            next_at_time = min(next_at_time, main_video.duration)

            if end_clip_time == 0 or end_clip_time < at_time:
                end_time = at_time

                video = create_reel_video_1(
                    main_video, None, subtitles, end_clip_time, end_time, template_id
                )

                if final_clip is not None:
                    final_clip = fade(final_clip, video)
                else:
                    final_clip = video

                end_clip_time = end_time

            if "search_terms" in data:

                clip = (
                    VideoFileClip(f"./temp/{video_id}/{clip_num}.mp4")
                    .resize((1280, 720))
                    .set_fps(24)
                    .set_audio(None)
                )
                clip_num += 1
            else:
                image = data["image"]
                image_path = f"./temp/{video_id}/image_{image}.jpg"
                clip = ImageClip(image_path, duration=5).resize((1280, 720)).set_fps(24)

            start_time = at_time if at_time >= end_clip_time else end_clip_time

            if (start_time + clip.duration) > next_at_time:
                end_time = next_at_time
            else:
                end_time = start_time + clip.duration

            time = end_time - start_time

            clip = clip.subclip(0, time)

            args = [main_video, clip, subtitles, start_time, end_time]

            video = temp_functions(*args)

            # selected_function = random.choice(transition_functions)
            final_clip = fade(final_clip, video, 0)
            end_clip_time = end_time

    if end_clip_time < main_video.duration:

        video = create_reel_video_3(
            main_video,
            subtitles,
            end_clip_time,
            main_video.duration,
            template_id,
        )

        final_clip = fade(final_clip, video)

    if os.path.exists(f"./temp/{video_id}/outro_video.mp4"):
        video = (
            VideoFileClip(f"./temp/{video_id}/outro_video.mp4")
            .resize((720, 1280))
            .set_fps(24)
        )
        final_clip = fade(final_clip, video)

    logo_path = f"./temp/{video_id}/logo.png"

    if not os.path.exists(logo_path):
        logo_path = "./asset/data/ciny_logo.png"

    position = logo.get("position", "top-right")
    size = logo.get("size", "medium")
    # Add logo
    logo, logo_pos = create_logo(
        final_clip,
        logo_path,
        position=position,
        size=size,
    )

    final_clip = CompositeVideoClip(
        [
            final_clip,
            logo.set_position(logo_pos),
        ]
    )

    # Final resize and export
    final_clip = final_clip.resize((720, 1280)).set_fps(24)

    if music_media_id:
        final_clip = music_service.add_music(video_id, final_clip, music_media_id)

    final_clip.write_videofile(
        f"./temp/{video_id}/{video_id}.mp4",
        threads=multiprocessing.cpu_count(),
        codec="libx264",
        preset="ultrafast",  # Faster encoding, larger file size
        ffmpeg_params=["-loglevel", "error", "-tune", "fastdecode"],
        logger=ProgressLogger(video_id, user_id),
    )
    duration = final_clip.duration

    final_clip.close()
    return f"./temp/{video_id}/{video_id}.mp4", duration


def test_reel_video(
    video_id: str,
    main_video: str,
    subtitles: str,
    clips,
    images,
    event_video,
    logo,
    music_media_id,
    user_id,
):

    end_clip_time = 0
    image_at_time = 0

    final_clip = None

    for index, clip in enumerate(clips):
        clip_duration = clip["clip_duration"]
        at_time = int(clip["atTime"])

        if at_time > main_video.duration:
            break

        if index < len(clips) - 1:
            next_at_time = int(clips[index + 1]["atTime"])
        else:
            next_at_time = main_video.duration

        if next_at_time > main_video.duration:
            next_at_time = main_video.duration

        if index < len(images):
            image = int(images[index]["image"])
            image_at_time = int(images[index]["atTime"])

        if end_clip_time == 0:
            end_time = at_time if at_time < image_at_time else 6

            final_clip = create_reel_video_1(main_video, None, subtitles, 0, end_time)
            end_clip_time = end_time

        if image_at_time < at_time and end_clip_time < at_time:

            image_path = f"./temp/{video_id}/image_{image}.jpg"

            clip = ImageClip(image_path, duration=(at_time - end_clip_time))

            clip = clip.resize(newsize=(900, 750))

            video = create_reel_video_1(
                main_video,
                clip.set_position((90, 200)),
                subtitles,
                end_clip_time,
                at_time,
            )

            final_clip = fade(final_clip, video)

            end_clip_time = at_time

        clip = event_video.subclip(*clip_duration)

        clip = clip.set_audio(None).resize((1280, 720)).set_fps(24)

        start_time = at_time if at_time >= end_clip_time else end_clip_time

        if (start_time + clip.duration) > next_at_time:
            end_time = next_at_time
        else:
            end_time = start_time + clip.duration

        time = end_time - start_time

        clip = clip.subclip(0, time)

        if index % 3 == 0:

            video = create_reel_video_4(
                main_video,
                clip.subclip(0, time),
                subtitles,
                start_time,
                end_time,
            )

        elif index % 3 == 1:

            clip = clip.crop(x1=150, y1=0, x2=1130, y2=720).resize(newsize=(900, 750))

            video = create_reel_video_1(
                main_video,
                clip.subclip(0, time).set_position((90, 200)),
                subtitles,
                start_time,
                end_time,
            )

        else:
            video = create_reel_video_2(
                main_video,
                clip.subclip(0, time).resize((1280, 720)),
                subtitles,
                start_time,
                end_time,
            )

        final_clip = fade(final_clip, video)
        end_clip_time = end_time

    if end_clip_time < main_video.duration:

        video = create_reel_video_3(
            main_video,
            subtitles,
            end_clip_time,
            main_video.duration,
        )

        final_clip = fade(final_clip, video)

    if os.path.exists(f"./temp/{video_id}/outro_video.mp4"):
        video = (
            VideoFileClip(f"./temp/{video_id}/outro_video.mp4")
            .resize((720, 1280))
            .set_fps(24)
        )
        final_clip = fade(final_clip, video)

    logo_path = f"./temp/{video_id}/logo.png"

    if not os.path.exists(logo_path):
        logo_path = "./asset/data/ciny_logo.png"

    position = logo.get("position", "top-right")
    size = logo.get("size", "medium")
    # Add logo
    logo, logo_pos = create_logo(
        final_clip,
        logo_path,
        position=position,
        size=size,
    )

    final_clip = CompositeVideoClip(
        [
            final_clip,
            logo.set_position(logo_pos),
        ]
    )

    # Final resize and export
    final_clip = final_clip.resize((720, 1280)).set_fps(24)

    if music_media_id:
        final_clip = music_service.add_music(video_id, final_clip, music_media_id)

    final_clip.write_videofile(
        f"./temp/{video_id}/{video_id}.mp4",
        threads=multiprocessing.cpu_count(),
        codec="libx264",
        preset="ultrafast",  # Faster encoding, larger file size
        ffmpeg_params=["-loglevel", "error", "-tune", "fastdecode"],
        logger=ProgressLogger(video_id, user_id),
    )
    duration = final_clip.duration

    final_clip.close()
    return f"./temp/{video_id}/{video_id}.mp4", duration


def test_reel_video1(
    video_id: str,
    custom_video_path: str,
    subtitles_path: str,
    images,
    video_data,
):
    # Load the main video and video clips
    main_video = VideoFileClip(custom_video_path)

    # Create a defaultdict to store the merged data, sorted by 'at_time'
    merged_data = defaultdict(list)

    # Add data1 items to the merged_data dictionary
    for item in images:
        merged_data[item["atTime"]].append({"image": item["image"]})

    # Add data2 items to the merged_data dictionary
    for item in video_data:
        merged_data[item["at_time"]].append({"search_terms": item["search_terms"]})

    # Sort the keys (at_time values) in increasing order
    sorted_keys = sorted(merged_data.keys())

    merged_json = [
        {"at_time": k, **{key: value for d in v for key, value in d.items()}}
        for k, v in zip(sorted_keys, [merged_data[key] for key in sorted_keys])
    ]

    print(merged_json)

    end_clip_time = 0

    final_clip = None

    clip_num = 0

    for index, data in enumerate(merged_json):

        at_time = int(data["at_time"])

        if index < len(merged_json) - 1:
            next_at_time = int(merged_json[index + 1]["at_time"])
        else:
            next_at_time = main_video.duration

        if end_clip_time == 0 or end_clip_time < at_time:
            end_time = at_time

            video = create_reel_video_1(
                main_video, None, subtitles_path, end_clip_time, end_time
            )

            if final_clip is not None:
                final_clip = fade(final_clip, video)
            else:
                final_clip = video

            end_clip_time = end_time

        if "image" in data:
            image = data["image"]
            image_path = f"./temp/{video_id}/image_{image}.jpg"
            clip = ImageClip(image_path, duration=4)

        else:
            clip = VideoFileClip(f"./temp/{video_id}/{clip_num}.mp4")
            clip_num += 1

        start_time = at_time if at_time >= end_clip_time else end_clip_time

        if (start_time + clip.duration) > next_at_time:
            end_time = next_at_time
        else:
            end_time = start_time + clip.duration

        time = end_time - start_time

        if "image" in data:

            clip = clip.resize(newsize=(900, 750))

            video = create_reel_video_1(
                main_video,
                clip.set_position((90, 200)).subclip(0, time),
                subtitles_path,
                start_time,
                end_time,
            )

        else:

            if clip_num % 3 == 0:

                video = create_reel_video_4(
                    main_video,
                    clip.subclip(0, time),
                    subtitles_path,
                    start_time,
                    end_time,
                )

            elif clip_num % 3 == 1:

                clip = clip.crop(x1=150, y1=0, x2=1130, y2=720).resize(
                    newsize=(900, 750)
                )

                video = create_reel_video_1(
                    main_video,
                    clip.subclip(0, time).set_position((90, 200)),
                    subtitles_path,
                    start_time,
                    end_time,
                )

            else:
                video = create_reel_video_2(
                    main_video,
                    clip.subclip(0, time).resize((1280, 720)),
                    subtitles_path,
                    start_time,
                    end_time,
                )

        final_clip = fade(final_clip, video)
        end_clip_time = end_time

    if end_clip_time < main_video.duration:

        video = create_reel_video_3(
            main_video,
            subtitles_path,
            end_clip_time,
            main_video.duration,
        )

        final_clip = fade(final_clip, video)

    final_clip = final_clip.resize((720, 1280)).set_fps(24)
    final_clip.write_videofile(
        f"./temp/{video_id}/{video_id}.mp4",
        threads=5,
        codec="libx264",
        preset="fast",
    )
    return f"./temp/{video_id}/{video_id}.mp4"


def create_reel_video1(
    video_id: str,
    user_id: str,
    audio_path: str,
    subtitles_path: str,
    clips,
    images,
    video_data,
    is_event_video,
    video_file_path,
    caption,
    music_media_id,
    logo,
):

    if video_file_path:
        event_video = VideoFileClip(video_file_path)

    # Load the main video and video clips
    main_audio = AudioFileClip(audio_path)

    # Create a defaultdict to store the merged data, sorted by 'at_time'
    merged_data = defaultdict(list)

    # Add data1 items to the merged_data dictionary
    for item in images:
        merged_data[item["atTime"]].append({"image": item["image"]})

    if is_event_video:
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

    # List of functions to choose from
    video_functions = [reel_video, landscape_to_portrait, landscape_to_portrait_full]

    end_clip_time = 0
    final_clip = None
    clip_num = 0

    for index, data in enumerate(merged_json):
        if "image" in data:
            image = data["image"]
            last_image_path = f"./temp/{video_id}/image_{image}.jpg"
            break

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

        if end_clip_time < at_time and end_clip_time != 0:
            duration = at_time - end_clip_time
            clip = (
                ImageClip(last_image_path, duration=duration)
                .resize((854, 480))
                .set_fps(24)
            )
            audio = main_audio.subclip(end_clip_time, at_time)

            clip = clip.set_audio(audio)

            video = landscape_to_portrait_full(main_audio, clip, end_clip_time, at_time)

            final_clip = fade(final_clip, video)

            end_clip_time = at_time

        if end_clip_time <= at_time or end_clip_time < next_at_time:

            if "clip" in data:
                clip_duration = data["clip_duration"]
                clip = (
                    event_video.subclip(*clip_duration).resize((854, 480)).set_fps(24)
                )
                end = (
                    next_at_time
                    if next_at_time < end_clip_time + clip.duration
                    and is_next_video_clip
                    else end_clip_time + clip.duration
                )
                if end > main_audio.duration:
                    end = main_audio.duration
                clip = clip.subclip(0, end - end_clip_time)
                start_time = end_clip_time
                end_time = end
                end_clip_time = end

            elif "image" in data:
                image = data["image"]
                image_path = f"./temp/{video_id}/image_{image}.jpg"
                duration = next_at_time - end_clip_time
                clip = (
                    ImageClip(image_path, duration=duration)
                    .resize((854, 480))
                    .set_fps(24)
                )
                start_time = end_clip_time
                end_time = next_at_time
                last_image_path = image_path
                end_clip_time = next_at_time
            else:
                clip = VideoFileClip(f"./temp/{video_id}/{clip_num}.mp4")
                end = (
                    next_at_time
                    if next_at_time < end_clip_time + clip.duration
                    else end_clip_time + clip.duration
                )
                clip = (
                    clip.subclip(0, end - end_clip_time).resize((854, 480)).set_fps(24)
                )
                start_time = end_clip_time
                end_time = end
                clip_num += 1
                end_clip_time = end

            # Randomly select a function
            selected_function = random.choice(video_functions)

            # Use the selected function
            video = selected_function(main_audio, clip, start_time, end_time)

            if final_clip:
                selected_function = random.choice(transition_functions)
                final_clip = selected_function(final_clip, video)
            else:
                final_clip = video

    if os.path.exists(f"./temp/{video_id}/outro_video.mp4"):
        video = (
            VideoFileClip(f"./temp/{video_id}/outro_video.mp4")
            .resize((480, 854))
            .set_fps(24)
        )
        final_clip = fade(final_clip, video)

    if caption:
        generator = create_text_generator(
            font_path=caption.get("font_path"),
            font_size=50,
            color=caption.get("color_code"),
        )
    else:
        # Pre-render subtitles
        generator = create_text_generator("./asset/font/bold_font.ttf", 50)

    subtitles = SubtitlesClip(subtitles_path, generator).set_duration(
        final_clip.duration
    )

    logo_path = f"./temp/{video_id}/logo.png"

    if not os.path.exists(logo_path):
        logo_path = "./asset/data/ciny_logo.png"

    position = logo.get("position", "top-right")
    size = logo.get("size", "medium")
    # Add logo
    logo, logo_pos = create_logo(final_clip, logo_path, position=position, size=size)

    final_clip = CompositeVideoClip(
        [
            final_clip,
            subtitles.subclip(0, final_clip.duration).set_position(("center", 500)),
            logo.set_position(logo_pos),
        ]
    )

    # Final resize and export
    final_clip = final_clip.resize((720, 1280)).set_fps(24)

    if music_media_id:
        final_clip = music_service.add_music(video_id, final_clip, music_media_id)

    final_clip.write_videofile(
        f"./temp/{video_id}/{video_id}.mp4",
        threads=multiprocessing.cpu_count(),
        codec="libx264",
        preset="ultrafast",  # Faster encoding, larger file size
        ffmpeg_params=["-loglevel", "error", "-tune", "fastdecode"],
        logger=ProgressLogger(video_id, user_id),
    )
    duration = final_clip.duration
    final_clip.close()
    return f"./temp/{video_id}/{video_id}.mp4", duration


def landscape_to_portrait(main_audio, video, start_time, end_time):

    audio = main_audio.subclip(start_time, end_time)

    # Get the original dimensions
    width = video.w

    crop_width = width // 2

    # Crop left and right portions
    left_crop = video.crop(x1=0, x2=crop_width).resize((480, 450))
    right_crop = video.crop(x1=width - crop_width, x2=width).resize((480, 450))

    # Create the final composite
    final_video = CompositeVideoClip(
        [
            left_crop.set_position(("center", "top")),
            right_crop.set_position(("center", "bottom")),
        ],
        size=(480, 854),
    )

    final_video = final_video.set_audio(audio)

    return final_video


def blur(image):
    return gaussian_filter(image, sigma=5)


def landscape_to_portrait_full(main_audio, video, start_time, end_time):

    audio = main_audio.subclip(start_time, end_time)

    # Get the original dimensions
    original_width, original_height = video.w, video.h

    # Calculate new dimensions (9:16 aspect ratio)
    new_height = int(original_width * 16 / 9)

    # Scale the video to fit the new width
    scaled_video = video.resize(width=original_width)

    # Calculate the height of the blurred sections
    blur_height = (new_height - original_height) // 2

    # Create a blurred-like effect for top and bottom
    blur_like_clip = (
        video.resize(height=blur_height)
        .crop(y1=0, y2=blur_height)
        .resize(width=original_width)  # Stretch horizontally
        .set_opacity(1)  # Add transparency
        # .fx(vfx.colorx, 1.5)  # Increase brightness
        .fl_image(blur)  # Apply custom blur function
    )

    # Create the final composite
    final_video = clips_array([[blur_like_clip], [scaled_video], [blur_like_clip]])

    final_video = final_video.resize((480, 854)).set_audio(audio)

    return final_video
