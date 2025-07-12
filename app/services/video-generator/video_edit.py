import numpy as np
import ffmpeg
import multiprocessing
import cv2
from moviepy.video.tools.drawing import circle
from moviepy.editor import VideoFileClip
import subprocess
import shlex
import os
import json
from PIL import Image, ImageDraw, ImageFont

import requests
from PIL import ImageEnhance
from io import BytesIO


def create_circular_mask(size, center, radius):
    height, width = size
    mask = np.zeros((height, width), dtype=np.float32)

    print(size, center, radius)
    # circle_mask = color_gradient(
    #     size, center, r=radius, col1=0.0, col2=1.0, shape="radial"
    # )
    circle_mask = circle(size, center=center, radius=radius)
    mask[:] = circle_mask
    return mask


# Define the circle mask
def circle_masks(frame, radius_percent, center=(1020, 540)):
    mask = np.zeros_like(frame, dtype=np.uint8)
    radius = int((min(frame.shape[1], frame.shape[0]) * radius_percent) / 100)
    cv2.circle(
        mask,
        center,
        radius,
        (255, 255, 255),
        -1,
    )
    return mask


def create_rounded_rectangle_mask(frame, img_shape, corner_radius):
    """
    Creates a mask image with a rounded rectangle shape.

    Args:
        img_shape (tuple): Shape of the output mask image (height, width).
        corner_radius (int): Radius of the rounded corners.

    Returns:
        numpy.ndarray: A binary mask image with the rounded rectangle shape.
    """

    x, y = (0, 0)
    w, h = img_shape

    mask = np.zeros_like(frame, dtype=np.uint8)

    # Create a rounded rectangle mask
    cv2.rectangle(
        mask,
        (x + corner_radius, y),
        (x + w - corner_radius, y + h),
        (255, 255, 255),
        -1,
        corner_radius,
    )
    cv2.rectangle(
        mask,
        (x, y + corner_radius),
        (x + w, y + h - corner_radius),
        (255, 255, 255),
        -1,
        corner_radius,
    )
    cv2.circle(
        mask, (x + corner_radius, y + corner_radius), corner_radius, (255, 255, 255), -1
    )
    cv2.circle(
        mask,
        (x + w - corner_radius, y + corner_radius),
        corner_radius,
        (255, 255, 255),
        -1,
    )
    cv2.circle(
        mask,
        (x + corner_radius, y + h - corner_radius),
        corner_radius,
        (255, 255, 255),
        -1,
    )
    cv2.circle(
        mask,
        (x + w - corner_radius, y + h - corner_radius),
        corner_radius,
        (255, 255, 255),
        -1,
    )

    return mask


def circle_mask_with_margins(video, radius_percent, margin_thickness=15):
    # Create a single image with the circle
    img = np.zeros((video.h, video.w, 4), dtype=np.uint8)  # Add an alpha channel

    radius = int(
        (
            min(video.get_frame(0).shape[1], video.get_frame(0).shape[0])
            // 2
            * radius_percent
        )
        / 100
    )

    cv2.circle(
        img, (540, 540), radius, (*(0, 0, 255), 255), margin_thickness
    )  # Set the alpha channel to 255

    return img


def circle_mask_with_margin(
    video, radius_percent, center=(1020, 540), margin_thickness=15
):
    # Create a single image with the circle
    img = np.zeros((video.h, video.w, 4), dtype=np.uint8)  # Add an alpha channel

    radius = int(
        (min(video.get_frame(0).shape[1], video.get_frame(0).shape[0]) * radius_percent)
        / 100
    )

    # Define the colors
    colors = [
        (25, 28, 255),  # 191cff
        (173, 52, 255),  # ad34ff
        (25, 28, 255),  # 191cff
        (8, 178, 225),  # 08b2e1
    ]
    x1, y1 = center

    for i in range(360):  # iterate over all degrees in a circle
        angle = i * 3.14159 / 180  # convert degree to radian
        x = int(x1 + radius * np.cos(angle))  # calculate x coordinate
        y = int(y1 + radius * np.sin(angle))  # calculate y coordinate

        # Calculate the color using interpolation
        color_index = int(i / 90) % len(colors)
        next_color_index = (color_index + 1) % len(colors)
        ratio = (i % 90) / 90.0
        r = int(
            colors[color_index][0] * (1 - ratio) + colors[next_color_index][0] * ratio
        )
        g = int(
            colors[color_index][1] * (1 - ratio) + colors[next_color_index][1] * ratio
        )
        b = int(
            colors[color_index][2] * (1 - ratio) + colors[next_color_index][2] * ratio
        )
        color = (r, g, b, 255)

        cv2.circle(
            img, (x, y), 1, color, margin_thickness
        )  # draw a small circle at the calculated position

    return img


def resize_video_moviepy(input_path, output_path, resolution="1080p"):

    if resolution == "4k":
        width, height = 3840, 2160
    elif resolution == "1080p":
        width, height = 1920, 1080
    else:
        raise ValueError("Unsupported resolution. Choose '4k' or '1080p'.")
    clip = VideoFileClip(input_path)
    resized_clip = clip.resize((width, height)).set_fps(30)
    resized_clip.write_videofile(
        output_path,
        threads=multiprocessing.cpu_count(),
        codec="libx264",
        preset="ultrafast",  # Faster encoding, larger file size
        ffmpeg_params=["-loglevel", "error", "-tune", "fastdecode"],
    )
    clip.close()
    resized_clip.close()


def resize_video_ffmpeg(input_path, output_path, resolution="1080p"):
    if resolution == "4k":
        width, height = 3840, 2160
    elif resolution == "1080p":
        width, height = 1920, 1080
    else:
        raise ValueError("Unsupported resolution. Choose '4k' or '1080p'.")
    stream = ffmpeg.input(input_path)
    stream = ffmpeg.filter(stream, "scale", width=width, height=height)
    stream = ffmpeg.filter(stream, "fps", fps=30)
    stream = ffmpeg.output(stream, output_path)
    ffmpeg.run(stream)


def upscale_video(
    input_path,
    output_path,
    is_landscape=True,
    resolution="1080p",
):
    """
    Upscale video from 720p to 1080p using FFmpeg with optimizations for speed.
    """

    if resolution == "4k":
        width, height = 3840, 2160
    elif resolution == "1080p":
        width, height = 1920, 1080
    else:
        raise ValueError("Unsupported resolution. Choose '4k' or '1080p'.")

    if not is_landscape:
        temp = width
        width = height
        height = temp
    try:
        # FFmpeg command for efficient upscaling
        command = (
            f"ffmpeg -i {shlex.quote(input_path)} "
            f"-vf scale={width}:{height}:flags=lanczos "
            f"-c:v libx264 -preset ultrafast -crf 23 "
            f"-c:a copy "
            f"{shlex.quote(output_path)}"
        )

        # Run the FFmpeg command
        subprocess.run(command, shell=True, check=True)

        print(f"Successfully upscaled video from {input_path} to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error upscaling video: {e}")
        raise


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

        # Extract the frame at the specified time
        frame = video.get_frame(time)

        # Save the frame as an image
        video.save_frame(output_path, t=time)

        print(f"Thumbnail created successfully: {output_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Make sure to close the video to free up resources
        video.close()


def enhance_image_quality(image_url, upscale_factor=10):
    """Enhances the image quality by adjusting brightness, contrast, sharpness, and color.

    Args:
        image_url (str): The URL of the image to enhance.

    Returns:
        PIL.Image: The enhanced image.
    """

    try:
        response = requests.get(
            image_url,
        )
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))

        print("image size", image.size)

        image = image.resize(
            (image.width * upscale_factor, image.height * upscale_factor)
        )

        print("image size", image.size)

        # Adjust brightness, contrast, sharpness, and color (adjust values as needed)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.2)  # Adjust brightness factor

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)  # Adjust contrast factor

        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)  # Adjust sharpness factor

        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.1)  # Adjust color saturation

        image.save("./temp/enhanced_image.jpg")
    except Exception as e:
        print(f"Error enhancing image: {e}")
        return None


def create_text_image(
    text,
    output_file,
    width=1920,
    height=1080,
    font_size=60,
    background_color="black",
    text_color="white",
):
    img = Image.new("RGB", (width, height), color=background_color)
    d = ImageDraw.Draw(img)

    # Try to use a default font
    try:
        # For Windows
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        try:
            # For macOS
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            try:
                # For Linux
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
                )
            except OSError:
                # If all else fails, use the default font
                font = ImageFont.load_default()
                print(
                    "Warning: Using default font. Text rendering quality may be affected."
                )

    # Get text size using font.getbbox() method
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position to center the text
    position = ((width - text_width) / 2, (height - text_height) / 2)

    # Draw the text
    d.text(position, text, fill=text_color, font=font)

    # Save the image
    img.save(output_file)


def create_video_template(config_file):
    with open(config_file, "r") as f:
        config = json.load(f)

    # Create temporary directory for assets
    os.makedirs("temp", exist_ok=True)

    # Create text slides
    for i, slide in enumerate(config["slides"]):
        create_text_image(
            slide["text"],
            f"temp/slide_{i}.png",
            background_color=slide.get("background_color", "black"),
            text_color=slide.get("text_color", "white"),
            font_size=slide.get("font_size", 60),
        )

    # Prepare FFmpeg command
    ffmpeg_command = ["ffmpeg", "-y"]
    filter_complex = []

    # Input all slides
    for i, slide in enumerate(config["slides"]):
        ffmpeg_command.extend(
            ["-loop", "1", "-t", str(slide["duration"]), "-i", f"temp/slide_{i}.png"]
        )

    # Create fade in/out effects for each slide
    for i in range(len(config["slides"])):
        filter_complex.append(
            f"[{i}:v]fade=t=in:st=0:d=1,fade=t=out:st={config['slides'][i]['duration']-1}:d=1[v{i}];"
        )

    # Add transitions between slides
    last_output = "v0"
    for i in range(1, len(config["slides"])):
        transition = config["transitions"][(i - 1) % len(config["transitions"])]
        filter_complex.append(
            f"[{last_output}][v{i}]xfade=transition={transition}:duration=1[v{i}out];"
        )
        last_output = f"v{i}out"

    # Finalize filter complex
    filter_complex_str = "".join(filter_complex)
    ffmpeg_command.extend(
        ["-filter_complex", filter_complex_str[:-1]]
    )  # Remove the last semicolon
    ffmpeg_command.extend(["-map", f"[{last_output}]"])
    ffmpeg_command.extend(
        [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-preset",
            "medium",
            "-crf",
            "23",
        ]
    )
    ffmpeg_command.append(config["output_file"])

    # Execute FFmpeg command
    print("Executing FFmpeg command:", " ".join(ffmpeg_command))
    subprocess.run(ffmpeg_command, check=True)

    print(f"Video template created successfully: {config['output_file']}")


def create_video_metadata(video_link, output_path, time=1):
    """
    Create a thumbnail image from a video file.

    :param video_path: Path to the input video file
    :param output_path: Path to save the output thumbnail image
    :param time: Time in seconds at which to extract the thumbnail (default is 0, the first frame)
    """
    try:

        # Load the video clip
        video = VideoFileClip(video_link)

        width, height = video.size

        video = video.resize((width / 2, height / 2))

        # Extract the frame at the specified time
        frame = video.get_frame(time)

        # Save the frame as an image
        video.save_frame(output_path, t=time)

        return video.size, video.duration

        print(f"Thumbnail created successfully: {output_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None, None
    finally:
        # Make sure to close the video to free up resources
        video.close()
