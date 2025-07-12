import sys
import os
from moviepy.editor import *
import numpy as np
from moviepy.video.fx.accel_decel import accel_decel
from moviepy.video.fx.blackwhite import blackwhite
from moviepy.video.fx.blink import blink
from moviepy.video.fx.crop import crop
from moviepy.video.fx.even_size import even_size
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.video.fx.freeze import freeze
from moviepy.video.fx.freeze_region import freeze_region
from moviepy.video.fx.gamma_corr import gamma_corr
from moviepy.video.fx.headblur import headblur
from moviepy.video.fx.invert_colors import invert_colors
from moviepy.video.fx.loop import loop
from moviepy.video.fx.lum_contrast import lum_contrast
from moviepy.video.fx.make_loopable import make_loopable
from moviepy.video.fx.margin import margin
from moviepy.video.fx.mask_and import mask_and
from moviepy.video.fx.mask_color import mask_color
from moviepy.video.fx.mask_or import mask_or
from moviepy.video.fx.mirror_x import mirror_x
from moviepy.video.fx.mirror_y import mirror_y
from moviepy.video.fx.painting import painting
from moviepy.video.fx.resize import resize
from moviepy.video.fx.rotate import rotate
from moviepy.video.fx.scroll import scroll
from moviepy.video.fx.supersample import supersample
from moviepy.video.fx.time_mirror import time_mirror
from moviepy.video.fx.time_symmetrize import time_symmetrize
from moviepy.video.fx.colorx import colorx


__all__ = (
    "accel_decel",
    "blackwhite",
    "blink",
    "crop",
    "even_size",
    "fadein",
    "fadeout",
    "freeze",
    "freeze_region",
    "gamma_corr",
    "headblur",
    "invert_colors",
    "loop",
    "lum_contrast",
    "make_loopable",
    "margin",
    "mask_and",
    "mask_color",
    "mask_or",
    "mirror_x",
    "mirror_y",
    "multiply_color",
    "multiply_speed",
    "painting",
    "resize",
    "rotate",
    "scroll",
    "supersample",
    "time_mirror",
    "time_symmetrize",
)

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def fade1(video1, video2, duration=1):
    """
    Perform a smooth fade transition between two videos without audio overlap.

    Args:
        video1 (VideoClip): First video clip.
        video2 (VideoClip): Second video clip.
        duration (int): Duration of the fade transition in seconds.

    Returns:
        CompositeVideoClip: The resulting video clip with smooth fade transition and no audio overlap.
    """
    # Cut the first video to end at the transition point
    video1_cut = video1.subclip(0, video1.duration - duration)

    # Cut the second video to start from the transition point
    video2_cut = video2.subclip(duration)

    # Create fade out effect for video1 (video only)
    fade_out = video1.subclip(video1.duration - duration).fx(
        vfx.fadeout, duration=duration
    )
    fade_out = fade_out.without_audio()

    # Create fade in effect for video2 (video only)
    fade_in = video2.subclip(0, duration).fx(vfx.fadein, duration=duration)
    fade_in = fade_in.without_audio()

    # Composite the videos with fade transition
    fade_transition = CompositeVideoClip(
        [
            video1_cut,
            fade_out.set_start(video1_cut.duration),
            fade_in.set_start(video1_cut.duration),
            video2_cut.set_start(video1.duration),
        ]
    )

    return fade_transition


def fade(video1, video2, duration=0.1):
    """
    Perform a smooth fade transition between two videos.

    Args:
        video1 (VideoClip): First video clip.
        video2 (VideoClip): Second video clip.
        duration (int): Duration of the fade transition in seconds.

    Returns:
        CompositeVideoClip: The resulting video clip with smooth fade transition.
    """
    # Ensure the second video starts exactly when the first one ends
    video2 = video2.set_start(video1.duration - duration)

    # Create a fade-out effect for the first video
    fade_out = video1.fx(fadeout, duration=duration)

    # Create a fade-in effect for the second video
    fade_in = video2.fx(fadein, duration=duration)

    # Composite the two videos with fade transition
    fade_transition = CompositeVideoClip([fade_out, fade_in])

    return fade_transition


def cross_dissolve(
    video1,
    video2,
    duration=0.3,
    foreground_position=(0.25, 0.25),
    foreground_opacity=0.7,
):
    """
    Perform a cross dissolve transition between two videos.

    Args:
        video1 (VideoClip): First video clip.
        video2 (VideoClip): Second video clip.
        duration (int): Duration of the cross dissolve transition in seconds.

    Returns:
        CompositeVideoClip: The resulting video clip with cross dissolve transition.
    """
    # Create a fade-out effect for the first video
    fade_out = video1.fx(fadeout, duration)

    # Create a fade-in effect for the second video
    fade_in = (
        video2.fx(fadein, duration)
        .set_position(foreground_position)
        .set_opacity(foreground_opacity)
    )

    # Composite the two videos with cross dissolve transition
    cross_dissolve_transition = CompositeVideoClip(
        [fade_out, fade_in.set_start(video1.duration - duration)]
    )

    return cross_dissolve_transition


def add_fade_in(video_file, output_file, duration=2):
    """
    Adds a fade-in effect to the video.

    Args:
        video_file (str): Path to the input video file.
        output_file (str): Path to the output video file.
        duration (float): Duration of the fade-in effect in seconds.
    """
    video = VideoFileClip(video_file)
    fade_in = video.fx(fadein, duration)
    fade_in.write_videofile(output_file)


def add_fade_out(video_file, output_file, duration=2):
    """
    Adds a fade-out effect to the video.

    Args:
        video_file (str): Path to the input video file.
        output_file (str): Path to the output video file.
        duration (float): Duration of the fade-out effect in seconds.
    """
    video = VideoFileClip(video_file)
    fade_out = video.fx(vfx.fadeout, duration)
    fade_out.write_videofile(output_file)


def add_gamma_correction(video, gamma=1.5):
    """
    Adds a gamma correction effect to the video.

    Args:
        video_file (str): Path to the input video file.
        output_file (str): Path to the output video file.
        gamma (float): Gamma value.
    """
    video = video.fx(gamma_corr, gamma)
    return video


def add_lum_contrast(video, lum=1.2, cont=1.5):
    """
    Adds a lum contrast effect to the video.

    Args:
        video_file (str): Path to the input video file.
        output_file (str): Path to the output video file.
        lum (float): Lum value.
        cont (float): Cont value.
    """

    video = video.fx(lum_contrast, lum, cont)
    return video


def add_rotate(video, angle=45):
    """
    Adds a rotate effect to the video.

    Args:
        video_file (str): Path to the input video file.
        output_file (str): Path to the output video file.
        angle (float): Rotation angle in degrees.
    """
    video = video.fx(rotate, angle)
    return video


def add_cross_dissolve_transition(video1, video2, duration):
    """
    Add a cross-dissolve transition between two videos

    Args:
        video1 (VideoFileClip): The first video
        video2 (VideoFileClip): The second video
        duration (float): The duration of the transition in seconds
    """
    # Calculate the start time of the transition
    start_time = max(0, video1.duration - duration)

    # Define the opacity functions
    def opacity1(t):
        return 1 - min(1, t / duration)

    def opacity2(t):
        return min(1, t / duration)

    # Apply the opacity functions to the videos
    video1_trans = (
        video1.set_start(start_time).set_duration(duration).set_opacity(opacity1)
    )
    video2_trans = (
        video2.set_start(start_time).set_duration(duration).set_opacity(opacity2)
    )

    # Create a composite video clip with the cross-dissolve transition
    transition_clip = CompositeVideoClip([video1_trans, video2_trans])

    # Return the resulting video
    return transition_clip


def add_burn_transition(video1_clip, video2_clip):
    """
    Add a video transition between two video clips.

    Args:
        video1 (str): Path to the first video file
        video2 (str): Path to the second video file
        transition_video (str): Path to the transition video file
        output (str): Path to the output video file
    """
    transition_clip = VideoFileClip("./asset/transitions/burn_trans.mp4")

    # Trim the transition clip to the desired duration
    transition_clip = transition_clip.subclip(0, 0.3)

    # Create a composite video clip with the transition
    composite_clip = CompositeVideoClip(
        [
            video1_clip,
            transition_clip.set_start(video1_clip.duration - 0.3),
            video2_clip.set_start(video1_clip.duration),
        ]
    )

    return composite_clip


def add_effect_transition(video1_clip, video2_clip):
    """
    Add a video transition between two video clips.

    Args:
        video1 (str): Path to the first video file
        video2 (str): Path to the second video file
        transition_video (str): Path to the transition video file
        output (str): Path to the output video file
    """
    transition_clip = VideoFileClip("./asset/transitions/effect.mp4")

    # Trim the transition clip to the desired duration
    transition_clip = transition_clip.subclip(0.5, 1).resize((1280, 720))

    # Create a composite video clip with the transition
    composite_clip = CompositeVideoClip(
        [
            video1_clip,
            transition_clip.set_start(video1_clip.duration - transition_clip.duration),
            video2_clip.set_start(video1_clip.duration),
        ]
    )

    return composite_clip


def add_multi_transition(video1_clip, video2_clip):
    """
    Add a video transition between two video clips.

    Args:
        video1 (str): Path to the first video file
        video2 (str): Path to the second video file
        transition_video (str): Path to the transition video file
        output (str): Path to the output video file
    """
    transition_clip = VideoFileClip("./asset/transitions/multi.mp4")

    # Trim the transition clip to the desired duration
    transition_clip = transition_clip.subclip(0, 0.5).resize((1280, 720))

    # Create a composite video clip with the transition
    composite_clip = CompositeVideoClip(
        [
            video1_clip,
            transition_clip.set_start(video1_clip.duration - transition_clip.duration),
            video2_clip.set_start(video1_clip.duration),
        ]
    )

    return composite_clip


def add_zoom_transition(video1_clip, video2_clip):
    """
    Add a video transition between two video clips.

    Args:
        video1 (str): Path to the first video file
        video2 (str): Path to the second video file
        transition_video (str): Path to the transition video file
        output (str): Path to the output video file
    """
    transition_clip = VideoFileClip("./asset/transitions/zoom.mp4")

    # Trim the transition clip to the desired duration
    transition_clip = transition_clip.subclip(0.1, 0.9).resize((1280, 720))

    # Create a composite video clip with the transition
    composite_clip = CompositeVideoClip(
        [
            video1_clip,
            transition_clip.set_start(video1_clip.duration - transition_clip.duration),
            video2_clip.set_start(video1_clip.duration),
        ]
    )

    return composite_clip


def add_video_transition(video1, video2, transition_video, output, transition_duration):
    """
    Add a video transition between two video clips.

    Args:
        video1 (str): Path to the first video file
        video2 (str): Path to the second video file
        transition_video (str): Path to the transition video file
        output (str): Path to the output video file
    """
    # Load the video clips
    video1_clip = VideoFileClip(video1).resize((1920, 1080))
    video2_clip = VideoFileClip(video2).resize((1920, 1080))
    transition_clip = VideoFileClip(transition_video)

    # Trim the transition clip to the desired duration
    transition_clip = transition_clip.subclip(
        0.5,
        (
            transition_duration
            if transition_clip.duration > transition_duration
            else transition_clip.duration
        ),
    ).resize((1920, 1080))

    # Create a composite video clip with the transition
    composite_clip = CompositeVideoClip(
        [
            video1_clip,
            transition_clip.set_start(video1_clip.duration - transition_duration),
            video2_clip.set_start(video1_clip.duration),
        ]
    )

    # Write the output video file
    composite_clip.write_videofile(output)


def add_text_and_image_animation(
    video_file, text, image_file, font_file, animation_duration
):
    # Load the video
    video = VideoFileClip(video_file)

    # Create a text clip
    text_clip = TextClip(text, fontsize=48, font=font_file, color="white")
    text_clip = text_clip.set_position("center").set_duration(animation_duration)

    # Create an image clip
    image_clip = ImageClip(image_file)
    image_clip = image_clip.set_position("center").set_duration(animation_duration)

    # Animate the text and image
    text_clip = text_clip.fx(fadein, 1).fx(fadeout, 1)
    image_clip = image_clip.fx(fadein, 1).fx(fadeout, 1)

    # Composite the text and image onto the video
    final_clip = CompositeVideoClip([video, text_clip, image_clip])

    # Write the output video
    final_clip.write_videofile("./asset/data/1.mp4")


def add_moving_text_animation(
    video_file, text, font_size, color, animation_duration, animation_type
):
    class MyScene(Scene):
        def construct(self):
            text_obj = Text(text, font_size=font_size, color=color)
            self.add(text_obj)

            if animation_type == "slide_in":
                self.play(text_obj.animate.shift(UP * 2), run_time=animation_duration)
            elif animation_type == "fade_in":
                self.play(text_obj.animate.set_opacity(1), run_time=animation_duration)
            else:
                raise ValueError("Invalid animation type")

    scene = MyScene()
    scene.render()
    return scene.renderer.file_name


def add_animation_transition(video1_clip, video2_clip):
    """
    Add a video transition between two video clips.

    Args:
        video1 (str): Path to the first video file
        video2 (str): Path to the second video file
        transition_video (str): Path to the transition video file
        output (str): Path to the output video file
    """
    transition_clip = VideoFileClip("./asset/transitions/animation.mp4").resize(
        (1280, 720)
    )

    # Trim the transition clip to the desired duration
    transition_clip = transition_clip.subclip(0.2, 0.4)

    # Create a composite video clip with the transition
    composite_clip = CompositeVideoClip(
        [
            video1_clip,
            transition_clip.set_start(video1_clip.duration - 0.4),
            video2_clip.set_start(video1_clip.duration),
        ]
    )

    return composite_clip


def add_slide_transitions(
    video1, video2, direction="right", duration=2, size_effect=True
):
    """
    Adds a slide transition between two videos.

    Args:
        video1 (VideoFileClip): The first input video clip.
        video2 (VideoFileClip): The second input video clip.
        direction (str): The direction of the slide transition. Can be 'right', 'left', 'top', 'bottom',
                         'top_left', 'top_right', 'bottom_left', or 'bottom_right'.
        duration (float): Duration of the transition effect in seconds.
    """

    # Calculate the width and height of the video
    width, height = video1.size

    video2 = video2.resize(video1.size)

    # Define the position function for each direction
    position_funcs = {
        "right": lambda t: (
            (width - t * width / duration, 0) if t < duration else (0, 0)
        ),
        "left": lambda t: (
            (-width + t * width / duration, 0) if t < duration else (0, 0)
        ),
        "top": lambda t: (
            (0, -height + t * height / duration) if t < duration else (0, 0)
        ),
        "bottom": lambda t: (
            (0, height - t * height / duration) if t < duration else (0, 0)
        ),
        "top_left": lambda t: (
            (-width + t * width / duration, -height + t * height / duration)
            if t < duration
            else (0, 0)
        ),
        "top_right": lambda t: (
            (width - t * width / duration, -height + t * height / duration)
            if t < duration
            else (0, 0)
        ),
        "bottom_left": lambda t: (
            (-width + t * width / duration, height - t * height / duration)
            if t < duration
            else (0, 0)
        ),
        "bottom_right": lambda t: (
            (width - t * width / duration, height - t * height / duration)
            if t < duration
            else (0, 0)
        ),
    }

    # Define the size function for corner transitions
    size_funcs = {
        "top_left": lambda t: (
            (t * width / duration, t * height / duration)
            if t < duration and t != 0
            else (width, height)
        ),
        "top_right": lambda t: (
            (t * width / duration, t * height / duration)
            if t < duration and t != 0
            else (width, height)
        ),
        "bottom_left": lambda t: (
            (t * width / duration, t * height / duration)
            if t < duration and t != 0
            else (width, height)
        ),
        "bottom_right": lambda t: (
            (t * width / duration, t * height / duration)
            if t < duration and t != 0
            else (width, height)
        ),
    }

    # Create a clip that slides in from the specified direction
    slide_clip = video2.set_position(position_funcs[direction])

    # Apply size effect for corner transitions
    if (
        direction in ["top_left", "top_right", "bottom_left", "bottom_right"]
        and size_effect
    ):
        slide_clip = slide_clip.set_start(0).resize(size_funcs[direction])

    # Composite the two clips
    transition = CompositeVideoClip(
        [video1, slide_clip.set_start(video1.duration - duration)]
    )

    return transition


def add_zoom_in_transition(
    video1, video2, direction="in", duration=0.1, position="center"
):
    """
    Adds a zoom in or zoom out transition between two videos.

    Args:
        video1 (VideoFileClip): The first input video clip.
        video2 (VideoFileClip): The second input video clip.
        direction (str): The direction of the zoom transition. Can be 'in' or 'out'.
        duration (float): Duration of the transition effect in seconds.
    """

    # Calculate the width and height of the video
    width, height = video1.size

    video2 = video2.resize(video1.size)

    # Define the zoom function for each direction
    zoom_funcs = {
        "in": lambda t: (t / duration) if t < duration and t != 0 else 1,
        "out": lambda t: (1 - t / duration) if t < duration else 0,
    }

    # Define the position function
    if position == "center":
        position_func = lambda t: ("center", "center")
    else:
        x, y = position
        position_func = lambda t: (x, y)

    # Create a clip that zooms in or out
    zoom_clip = (
        video2.set_start(video1.duration - duration)
        .resize(zoom_funcs[direction])
        .set_position(position_func)
    )

    # Composite the two clips
    transition = CompositeVideoClip(
        [video1, zoom_clip.set_start(video1.duration - duration)]
    )

    return transition


def add_zoom_out_transition(
    video1, video2, direction="in", duration=0.1, position="center", rotation=False
):
    """
    Adds a zoom in or zoom out transition between two videos.

    Args:
        video1 (VideoFileClip): The first input video clip.
        video2 (VideoFileClip): The second input video clip.
        direction (str): The direction of the zoom transition. Can be 'in' or 'out'.
        duration (float): Duration of the transition effect in seconds.
    """

    # Calculate the width and height of the video
    width, height = video1.size

    video2 = video2.resize(video1.size)

    # Define the zoom function for each direction
    zoom_funcs = {
        "in": lambda t: (
            (1 + 25 * (t - (video1.duration - duration)) / video1.duration)
            if t >= (video1.duration - duration)
            else 1
        ),
        "out": lambda t: (1 - t / duration) if t < duration else 0,
    }

    # Define the position function
    if position == "center":
        position_func = lambda t: ("center", "center")
    else:
        x, y = position
        position_func = lambda t: (x, y)

    # Define the rotation function for each direction
    if rotation:
        rotation_func = lambda t: ((360 * t / duration) % 360)
    else:
        rotation_func = lambda t: -(360 * t / duration) % 360

    if rotation:
        # Create a clip that rotates
        zoom_clip = (
            video1.set_start(video1.duration)
            .resize(zoom_funcs[direction])
            .rotate(rotation_func)
            .set_position(position_func)
        )

    else:

        # Create a clip that zooms in or out
        zoom_clip = (
            video1.set_duration(video1.duration)
            .resize(zoom_funcs[direction])
            .set_position(position_func)
        )

    # Composite the two clips
    transition = CompositeVideoClip([zoom_clip, video2.set_start(video1.duration)])

    return transition


def add_rotation_transition(video1, video2, direction="clockwise", duration=1):
    """
    Adds a rotation transition between two videos.

    Args:
        video1 (VideoFileClip): The first input video clip.
        video2 (VideoFileClip): The second input video clip.
        direction (str): The direction of rotation. Can be 'clockwise' or 'counterclockwise'.
        duration (float): Duration of the transition effect in seconds.

    Returns:
        CompositeVideoClip: The resulting video clip with the rotation transition applied.
    """
    # Calculate the width and height of the video
    width, height = video1.size

    video2 = video2.resize(video1.size)

    # Define the rotation function for each direction
    if direction == "clockwise":
        rotation_func = lambda t: (
            (360 * t / duration) % 360 if t > (video1.duration - duration) else 360
        )
    else:
        rotation_func = lambda t: -(360 * t / duration) % 360

    position_func = lambda t: ("center", "center")

    # Define the zoom function for each direction
    zoom_func = lambda t: (
        (1 + 20 * (t - (video1.duration - duration)) / video1.duration)
        if t >= (video1.duration - duration)
        else 1
    )

    # Composite the two clips
    transition = CompositeVideoClip(
        [
            video1.resize(zoom_func).rotate(rotation_func).set_position(position_func),
            video2.set_start(video1.duration),
        ]
    )

    return transition


def cross_dissolve_test(
    video1, video2, duration=1, foreground_position=(0.50, 0.50), foreground_opacity=1
):
    """
    Perform a cross dissolve transition between two videos.

    Args:
        video1 (VideoClip): First video clip.
        video2 (VideoClip): Second video clip.
        duration (int): Duration of the cross dissolve transition in seconds.

    Returns:
        CompositeVideoClip: The resulting video clip with cross dissolve transition.
    """

    # Create a fade-in effect for the second video
    fade_in = (
        video2.fx(fadein, duration)
        .set_position(foreground_position)
        .set_opacity(foreground_opacity)
    )

    # Create a fade-in effect for the second video
    video1 = video1.set_position(foreground_position).set_opacity(2)

    # Composite the two videos with cross dissolve transition
    cross_dissolve_transition = CompositeVideoClip([video1, fade_in])

    return cross_dissolve_transition


def add_crossfade_transition(
    clip1,
    clip2,
    crossfade_duration=1.0,
):
    """
    Add a crossfade transition between two video clips and merge them into one.

    Parameters:
    -----------
    clip1_path : str
        Path to the first video clip
    clip2_path : str
        Path to the second video clip
    output_path : str
        Path where the output video will be saved
    crossfade_duration : float, optional
        Duration of the crossfade transition in seconds (default: 1.0)

    Returns:
    --------
    None
        The function saves the processed video to the output_path
    """
    try:

        # Get the duration of the first clip
        clip1_duration = clip1.duration

        # Create the fade out effect for the first clip
        clip1_fadeout = clip1.copy().set_end(clip1_duration)
        clip1_fadeout = clip1_fadeout.crossfadeout(crossfade_duration)

        # Create the fade in effect for the second clip
        clip2_fadein = clip2.copy()
        clip2_fadein = clip2_fadein.crossfadein(crossfade_duration)

        # Position the second clip to start at the appropriate time
        clip2_fadein = clip2_fadein.set_start(clip1_duration - crossfade_duration)

        # Combine the clips
        final_clip = CompositeVideoClip([clip1_fadeout, clip2_fadein])

        return final_clip

    except Exception as e:
        print(f"Error processing video: {str(e)}")


def crossfade_multiple_clips(
    clips,
    crossfade_duration=1.0,
):
    """
    Add crossfade transitions between multiple video clips and combine them.

    Parameters:
    -----------
    clip_paths : list
        List of paths to video clips in order
    output_path : str
        Path where the output video will be saved
    crossfade_duration : float, optional
        Duration of each crossfade transition in seconds (default: 1.0)

    Returns:
    --------
    None
        The function saves the processed video to the output_path
    """
    try:
        if len(clip_paths) < 2:
            raise ValueError("Need at least 2 clips to create transitions")

        # Calculate the start times for each clip
        durations = [clip.duration for clip in clips]
        start_times = [0]
        for i in range(1, len(durations)):
            # Each clip starts at the end of the previous clip minus the crossfade duration
            start_times.append(
                start_times[i - 1] + durations[i - 1] - crossfade_duration
            )

        # Create a list to hold all the clips with their position/transition
        positioned_clips = []

        for i, clip in enumerate(clips):
            if i == 0:
                # First clip fades out
                modified_clip = clip.copy().crossfadeout(crossfade_duration)
            elif i == len(clips) - 1:
                # Last clip fades in
                modified_clip = clip.copy().crossfadein(crossfade_duration)
            else:
                # Middle clips fade in and out
                modified_clip = (
                    clip.copy()
                    .crossfadein(crossfade_duration)
                    .crossfadeout(crossfade_duration)
                )

            # Set the start time for this clip
            modified_clip = modified_clip.set_start(start_times[i])

            positioned_clips.append(modified_clip)

        # Combine all clips
        final_clip = CompositeVideoClip(positioned_clips)

        return final_clip

    except Exception as e:
        print(f"Error processing videos: {str(e)}")


def add_slow_fades(
    video,
    fade_in_duration=0.2,
    fade_out_duration=0.2,
):
    """
    Add slow, gradual fade-in and fade-out effects to a video clip.

    Parameters:
    -----------
    video_path : str
        Path to the input video file
    output_path : str
        Path where the output video will be saved
    fade_in_duration : float, optional
        Duration of the fade-in effect in seconds (default: 3.0)
    fade_out_duration : float, optional
        Duration of the fade-out effect in seconds (default: 3.0)

    Returns:
    --------
    None
        The function saves the processed video to the output_path
    """
    try:

        # Get the total duration of the video
        total_duration = video.duration

        # Create a custom fade-in effect with a more gradual curve
        # This creates a slow, gentle fade instead of the default linear fade
        def slow_fadein(t):
            # Using a quadratic function for a smoother, slower start
            if t < fade_in_duration:
                return np.sqrt(t / fade_in_duration)
            else:
                return 1.0

        # Create a custom fade-out effect with a more gradual curve
        def slow_fadeout(t):
            # Using a quadratic function for a smoother, slower end
            if t > total_duration - fade_out_duration:
                remaining = total_duration - t
                return np.sqrt(remaining / fade_out_duration)
            else:
                return 1.0

        # Apply both fade effects
        video_with_fades = video.fl(
            lambda gf, t: gf(t) * slow_fadein(t) * slow_fadeout(t)
        )

        return video_with_fades

    except Exception as e:
        print(f"Error processing video: {str(e)}")


def slow_crossfade_multiple_clips(clips, crossfade_duration=3.0):
    """
    Add slow, gradual crossfade transitions between multiple video clips.

    Parameters:
    -----------
    clip_paths : list
        List of paths to video clips in order
    output_path : str
        Path where the output video will be saved
    crossfade_duration : float, optional
        Duration of each crossfade transition in seconds (default: 3.0)

    Returns:
    --------
    None
        The function saves the processed video to the output_path
    """
    try:

        # Function to create a slow, custom fadeout curve
        def custom_fadeout(clip, duration):
            def fading(t):
                # Using a power function for a more gradual fade
                if t > clip.duration - duration:
                    remaining = clip.duration - t
                    return (
                        remaining / duration
                    ) ** 0.7  # The 0.7 power makes it more gradual
                else:
                    return 1.0

            return clip.fl(lambda gf, t: gf(t) * fading(t))

        # Function to create a slow, custom fadein curve
        def custom_fadein(clip, duration):
            def fading(t):
                # Using a power function for a more gradual fade
                if t < duration:
                    return (t / duration) ** 0.7  # The 0.7 power makes it more gradual
                else:
                    return 1.0

            return clip.fl(lambda gf, t: gf(t) * fading(t))

        # Calculate the start times for each clip
        final_clips = []
        current_end = 0

        for i, clip in enumerate(clips):
            start_time = current_end - crossfade_duration if i > 0 else 0

            # Apply custom fades
            if i == 0:  # First clip
                processed_clip = custom_fadeout(clip, crossfade_duration)
            elif i == len(clips) - 1:  # Last clip
                processed_clip = custom_fadein(clip, crossfade_duration)
            else:  # Middle clips
                processed_clip = custom_fadein(
                    custom_fadeout(clip, crossfade_duration), crossfade_duration
                )

            # Position the clip
            positioned_clip = processed_clip.set_start(start_time)
            final_clips.append(positioned_clip)

            # Update the end time for the next clip
            current_end = start_time + clip.duration

        # Combine all clips
        final_video = CompositeVideoClip(final_clips)

        return final_video

    except Exception as e:
        print(f"Error processing videos: {str(e)}")


# # Example of crossfade between two clips
# final_clip = add_slow_fades(
#     VideoFileClip("./temp/test.mp4").subclip(0, 5),
#     # VideoFileClip("./temp/test.mp4").subclip(0, 5),
#     # crossfade_duration=1.5,
# )

# # Example of crossfades between multiple clips
# clip_paths = ["clip1.mp4", "clip2.mp4", "clip3.mp4", "clip4.mp4"]
# crossfade_multiple_clips(
#     clip_paths, "output_multiple_crossfades.mp4", crossfade_duration=1.0
# )

# final_clip.write_videofile(
#     "./temp/test22.mp4",
#     threads=4,
#     codec="libx264",
#     preset="ultrafast",  # Faster encoding, larger file size
#     ffmpeg_params=["-loglevel", "error", "-tune", "fastdecode"],
# )
