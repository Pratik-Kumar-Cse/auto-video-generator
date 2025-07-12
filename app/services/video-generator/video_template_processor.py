from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, clips_array  # type: ignore
from moviepy.video.fx.resize import resize  # type: ignore
from scipy.ndimage import gaussian_filter
import numpy as np  # type: ignore
from PIL import Image, ImageFilter
import cv2
from typing import Tuple, Union, Literal
import os
from .utils import add_zoom_effect
from .transition import add_slow_fades
from app.loggers.progress_logger import ProgressLogger
from app.templates.video.video_templates_payload import VIDEO_TEMPLATES


class VideoTemplateProcessor:
    def __init__(self, template_id="template_1"):
        """
        Initialize VideoTemplateProcessor with a specified template.

        Parameters:
        - template_id (str): Identifier for the video template to use.
        """
        self.template = VIDEO_TEMPLATES[template_id]
        self.width = self.template["resolution"]["width"]
        self.height = self.template["resolution"]["height"]
        self.duration = None
        self.blur_amount = 60
        self.main_clip = None

    # [Previous helper methods remain unchanged]
    def create_blurred_background(self, clip):
        """
        Create a blurred background from a frame of the main content video.

        Parameters:
        - clip (VideoFileClip): The video clip to use for generating the blurred background.

        Returns:
        - ImageClip: Blurred background clip matching the dimensions of the template.
        """
        # Get a frame in the middle of the video
        frame_number = int(clip.fps * clip.duration / 2)
        frame = clip.get_frame(frame_number / clip.fps)  # Extract the frame
        blurred_frame = self.apply_blur_to_frame(
            frame, blur_amount=self.blur_amount
        )  # Apply blur

        # Create a new ImageClip from the blurred frame
        blurred_background = ImageClip(blurred_frame).set_duration(clip.duration)
        blurred_background = blurred_background.resize(
            (self.width, self.height)
        )  # Resize to template
        blurred_background = (
            blurred_background.without_audio()
        )  # Remove audio from the background clip
        return blurred_background

    def apply_blur_to_frame(self, frame, blur_amount):
        """
        Apply Gaussian blur to a given frame.

        Parameters:
        - frame (numpy.ndarray): The frame to blur.
        - blur_amount (int): The amount of Gaussian blur to apply.

        Returns:
        - numpy.ndarray: The blurred frame as a NumPy array.
        """
        img = Image.fromarray(frame)  # Convert frame to PIL Image
        blurred = img.filter(
            ImageFilter.GaussianBlur(blur_amount)
        )  # Apply Gaussian blur
        return np.array(blurred)  # Convert back to NumPy array

    def create_circular_mask(self, size, border_width=8):
        """
        Create a circular mask with a gradient border using 4 colors.

        Parameters:
        - size (tuple): The dimensions of the mask (height, width).
        - border_width (int): The thickness of the circular border.

        Returns:
        - numpy.ndarray: The circular mask as a NumPy array.
        """
        height, width = size
        center_x, center_y = width // 2, height // 2
        radius = min(center_x, center_y)
        y, x = np.ogrid[:height, :width]
        dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

        # Create a 4-channel RGBA image for the mask
        mask = np.zeros((height, width, 4), dtype=np.uint8)

        # Define colors (RGB format from hex)
        colors = [
            (0xDC, 0x64, 0xF7, 255),  # Purple (DC64F7) at 0°
            (0x00, 0xD3, 0xAE, 255),  # Turquoise (00D3AE) at 45°
            (0xFF, 0x5A, 0x3A, 255),  # Red-Orange (FF5A3A) at 90°
            (0xFF, 0xB0, 0x20, 255),  # Orange (FFB020) at 135°
            (0xDC, 0x64, 0xF7, 255),  # Purple again at 360° for smooth transition
        ]

        # Create the border
        outer_radius = radius
        inner_radius = radius - border_width
        border_area = (dist_from_center <= outer_radius) & (
            dist_from_center > inner_radius
        )

        # Calculate angles for each point from center
        angles = np.arctan2(y - center_y, x - center_x)
        angles_deg = np.degrees(angles) % 360

        def interpolate_color(angle):
            """
            Interpolate between colors based on angle.
            """
            # Define color stops at specific angles
            color_stops = [
                (0, colors[0]),  # Purple at 0°
                (45, colors[1]),  # Turquoise at 45°
                (90, colors[2]),  # Red-Orange at 90°
                (135, colors[3]),  # Orange at 135°
                (360, colors[0]),  # Purple at 360°
            ]

            # Find the two colors to interpolate between
            for i in range(len(color_stops) - 1):
                angle1, color1 = color_stops[i]
                angle2, color2 = color_stops[i + 1]

                if angle1 <= angle <= angle2:
                    # Calculate interpolation factor
                    factor = (angle - angle1) / (angle2 - angle1)

                    # Interpolate each color channel
                    result = []
                    for j in range(4):  # RGBA channels
                        value = int(color1[j] * (1 - factor) + color2[j] * factor)
                        result.append(value)
                    return tuple(result)

            return colors[0]  # Default return

        # Apply gradient to border
        for y in range(height):
            for x in range(width):
                if border_area[y, x]:
                    angle = angles_deg[y, x]
                    mask[y, x] = interpolate_color(angle)

        # Fill the inner circle with white
        inner_area = dist_from_center <= inner_radius
        mask[inner_area] = (255, 255, 255, 255)  # White with full opacity

        return mask

    def create_rounded_rectangle_mask(self, frame, img_shape, corner_radius):
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
            mask,
            (x + corner_radius, y + corner_radius),
            corner_radius,
            (255, 255, 255),
            -1,
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

    def convert_video_aspect_ratio(
        self,
        video,
        target_ratio: Literal["9:16", "16:9"] = "9:16",
        focus_position: Literal["center", "left", "right"] = "center",
        custom_position: float = None,
    ) -> None:
        """
        Convert video aspect ratio, specifically handling 16:9 to 9:16 conversion.

        Args:
            video (str): Path to input video file
            target_ratio (str): Target aspect ratio ("9:16" or "16:9")
            focus_position (str): Where to focus the crop ("center", "left", "right")
            custom_position (float): Custom horizontal position (0-1) for crop center

        Returns:
            None: Saves the processed video to output_path
        """

        orig_width, orig_height = video.size

        # Calculate dimensions for 9:16 or 16:9
        if target_ratio == "9:16":
            # Convert to portrait (9:16)
            new_height = orig_height
            new_width = int((9 / 16) * new_height)
        else:
            # Convert to landscape (16:9)
            new_width = orig_width
            new_height = int((9 / 16) * new_width)

        # Calculate crop position
        if custom_position is not None:
            # Use custom position (0-1 range)
            x_center = int((orig_width - new_width) * max(0, min(1, custom_position)))
        else:
            if focus_position == "center":
                x_center = (orig_width - new_width) // 2
            elif focus_position == "left":
                x_center = 0
            else:  # right
                x_center = orig_width - new_width

        # Crop the video
        cropped_video = video.crop(
            x1=x_center, x2=x_center + new_width, y1=0, y2=orig_height
        )

        return cropped_video

    def resize_video_by_crop(
        self,
        video,
        target_size: Tuple[int, int],
        crop_center: bool = True,
        crop_position: Tuple[Union[int, float], Union[int, float]] = (0, 0),
    ) -> None:
        """
        Resize a video by cropping without compression, maintaining original quality.

        Args:
            video (str): Path to input video file
            target_size (tuple): Desired output size as (width, height)
            crop_center (bool): If True, crop from center. If False, use crop_position
            crop_position (tuple): (x, y) coordinates for top-left corner of crop
        """

        orig_width, orig_height = video.size
        target_width, target_height = target_size

        if target_width > orig_width or target_height > orig_height:
            raise ValueError(
                f"Target size {target_size} cannot be larger than original size {video.size}"
            )

        if crop_center:
            x1 = (orig_width - target_width) // 2
            y1 = (orig_height - target_height) // 2
        else:
            x1, y1 = crop_position
            if isinstance(x1, float) and 0 <= x1 <= 1:
                x1 = int(x1 * orig_width)
            if isinstance(y1, float) and 0 <= y1 <= 1:
                y1 = int(y1 * orig_height)

        x1 = max(0, min(x1, orig_width - target_width))
        y1 = max(0, min(y1, orig_height - target_height))

        cropped_video = video.crop(
            x1=x1, y1=y1, x2=x1 + target_width, y2=y1 + target_height
        )

        return cropped_video

    def create_logo_background(self, size, logo_path):
        """
        Place a logo image at a specific position with transparent background.

        Parameters:
        - size (tuple): The size of the output image (width, height)
        - logo_path (str): Path to the logo image file

        Returns:
        - numpy.ndarray: The logo as a NumPy array
        """
        # Create a transparent background
        img = Image.new("RGBA", size, (0, 0, 0, 0))

        # Open and resize logo image
        logo = Image.open(logo_path).convert("RGBA")
        width, height = size
        logo = logo.resize(
            (int(width * 1), int(height * 1)), Image.Resampling.LANCZOS
        )  # Adjust size as needed

        # Calculate position to place it in bottom right corner
        logo_pos = (width - logo.width, height - logo.height)

        # Paste logo onto transparent background
        img.paste(logo, logo_pos, logo)

        return np.array(img)

    def blur(self, image):
        return gaussian_filter(image, sigma=5)

    def landscape_to_portrait_full(self, video):

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
            .fl_image(self.blur)  # Apply custom blur function
        )

        # Create the final composite
        final_video = clips_array([[blur_like_clip], [scaled_video], [blur_like_clip]])

        return final_video

    def process_element(self, element, clip_data_object):
        """
        Process individual elements of the video template.

        Parameters:
        - element (dict): Element data from the template (e.g., video, image).
        - clip_data_object (dict): Data object containing video clips or source paths.

        Returns:
        - VideoFileClip or ImageClip: Processed video or image clip.
        """
        if element["type"] == "video":  # Process video elements
            clip = clip_data_object.get("video_clip")  # Get the video clip

            if element["id"] == "background":  # Handle background element
                if self.duration is None:
                    self.duration = clip.duration  # Set duration if not already set
                clip = resize(
                    clip, width=self.width, height=self.height
                )  # Resize to fit template
                clip = clip.loop(duration=self.duration)  # Loop clip for full duration

            elif element["id"] == "main":  # Handle main content element
                self.main_clip = clip  # Store main content clip
                pos = element["position"]
                target_diameter = pos["width"]  # Desired size for the main content
                orig_w, orig_h = clip.size
                scale = max(
                    target_diameter / orig_w, target_diameter / orig_h
                )  # Calculate scale
                new_size = (int(orig_w * scale), int(orig_h * scale))  # Resize the clip
                clip = resize(clip, new_size)

                # Calculate cropping coordinates to center the clip
                x1 = (new_size[0] - target_diameter) // 2
                y1 = (new_size[1] - target_diameter) // 2
                clip = clip.crop(
                    x1=x1,
                    y1=y1,
                    width=target_diameter,
                    height=target_diameter,  # Crop to target size
                )

                if (
                    "mask" in element and element["mask"]["type"] == "circle"
                ):  # Check for circular mask
                    # Create mask with border
                    mask = self.create_circular_mask((target_diameter, target_diameter))

                    # Create a mask clip for the content area (white part of the mask)
                    content_mask = (
                        (mask == [255, 255, 255, 255]).all(axis=2).astype(np.uint8)
                    )
                    mask_clip = ImageClip(
                        content_mask, ismask=True, duration=clip.duration
                    )

                    # Apply the content mask to the video
                    masked_clip = clip.set_mask(mask_clip)

                    # Create a clip for the border
                    border_clip = ImageClip(
                        mask, transparent=True, duration=clip.duration
                    )

                    # Composite the border and masked video
                    clip = CompositeVideoClip(
                        [border_clip, masked_clip], use_bgclip=False
                    )

                # Determine x position based on left, centerX, or right
                if "left" in pos:
                    x = pos["left"]  # Align to the left
                elif "right" in pos:
                    x = (
                        self.width - target_diameter - pos["right"]
                    )  # Align to the right
                else:
                    x = (self.width - target_diameter) // 2  # Center by default

                # Calculate y position (bottom alignment as before)
                y = self.height - target_diameter - pos.get("bottom", 0)

                # Set the position of the clip
                clip = clip.set_position((x, y))

                # Loop or set duration based on the longest clip
                if not self.duration:
                    self.duration = clip.duration
                if clip.duration < self.duration:
                    clip = clip.loop(duration=self.duration)

            elif element["id"] == "clip":
                size = element["size"]
                position = element["position"]
                mask = element["mask"]

                if mask["enabled"]:
                    # Generate the mask image
                    mask_image = self.create_rounded_rectangle_mask(
                        clip.get_frame(0), clip.size, 65
                    )
                    # Apply the circle mask to the video
                    mask_clip = ImageClip(mask_image, ismask=True)
                    # Apply a mask (circular for video2, square for video1 is by default)
                    clip = clip.set_mask(mask_clip)

                if size["aspectRatio"] == "9:16":
                    # clip = self.convert_video_aspect_ratio(video=clip)
                    # Scale the video to fit the new width
                    if clip.w > clip.h:
                        clip = self.landscape_to_portrait_full(clip)

                clip = clip.resize((size["width"], size["height"])).set_position(
                    (position["x"], position["y"])
                )

            return clip

        if element["type"] == "audio":
            return clip_data_object.get("audio_clip")

        elif element["type"] == "image":  # Process image elements
            pos = element["position"]
            source_path = clip_data_object.get("source_path")  # Get image path

            # Load the image as an ImageClip
            if element.get("style", {}).get("circle"):
                img_array = self.create_logo_background(
                    (pos["width"], pos["height"]), source_path
                )
                clip = ImageClip(img_array)
            else:
                clip = ImageClip(source_path)
                clip = clip.resize(
                    width=pos["width"], height=pos["height"]
                )  # Resize image to template dimensions
            x = self.width - pos["width"] - pos["right"]
            y = pos["top"]
            if self.duration:
                clip = clip.set_duration(self.duration)
            return clip.set_position((x, y))

    def generate_video(
        self,
        source_files,
        video_id,
    ):
        """
        Generate a video using the specified template and clips.

        Parameters:
        - clip_data_object (dict): Data object containing video clips and source paths.

        Returns:
        - CompositeVideoClip: The final generated video.
        """

        output_path = f"./temp/{video_id}/{video_id}.mp4"
        all_clips = []
        current_time = 0
        main_clip = None

        intro_path = f"./temp/{video_id}/intro_video.mp4"
        outro_path = f"./temp/{video_id}/outro_video.mp4"
        logo_path = f"./temp/{video_id}/logo.png"

        intro_clip = VideoFileClip(intro_path) if os.path.exists(intro_path) else None
        outro_clip = VideoFileClip(outro_path) if os.path.exists(outro_path) else None
        logo = logo_path if os.path.exists(logo_path) else None

        try:
            # 1. Process intro clip
            if intro_clip:
                intro_clip = intro_clip.resize((self.width, self.height))
                intro_duration = intro_clip.duration
                intro_clip = intro_clip.set_start(0)  # Start at beginning
                all_clips.append(intro_clip)
                current_time += intro_duration

            # 2. Process main content section
            main_section_clips = []

            if "main_video" in source_files or "main_audio" in source_files:
                intro_time = current_time
                # Process main content
                if "main_video" in source_files:
                    main_video = next(
                        (
                            e
                            for e in self.template["elements"]
                            if e["id"] == "main_video"
                        ),
                        None,
                    )
                    if main_video:
                        main_clip = self.process_element(
                            main_video, {"video_clip": source_files["main_video"]}
                        )

                        self.duration = main_clip.duration

                elif "main_audio" in source_files:
                    main_audio = next(
                        (
                            e
                            for e in self.template["elements"]
                            if e["id"] == "main_audio"
                        ),
                        None,
                    )
                    if main_audio:
                        main_audio_clip = self.process_element(
                            main_audio, {"audio_clip": source_files["main_audio"]}
                        )

                        self.duration = main_audio_clip.duration
                print("audio and video", 594)
                if main_clip:
                    # Add background (either from video or blurred)
                    if "background" in source_files:
                        background_element = next(
                            (
                                e
                                for e in self.template["elements"]
                                if e["id"] == "background"
                            ),
                            None,
                        )
                        if background_element:
                            background_clip = self.process_element(
                                background_element,
                                {"video_clip": source_files["background"]},
                            )
                            background_clip = background_clip.set_start(current_time)
                            main_section_clips.append(background_clip)
                    else:
                        background_clip = self.create_blurred_background(self.main_clip)
                        background_clip = background_clip.set_start(current_time)
                        main_section_clips.append(background_clip)

                print("background", 618)
                if "stock" in source_files:
                    clip_element = next(
                        (e for e in self.template["elements"] if e["id"] == "clip"),
                        None,
                    )
                    end_time = 0

                    stock_video_placement = source_files["stock"]
                    image_index = 1
                    video_index = 0
                    for index, stock_video in enumerate(stock_video_placement):
                        video_start_time = 0
                        start_time = stock_video["atTime"]
                        if start_time > self.duration:
                            break

                        if index < len(stock_video_placement) - 1:
                            next_time = stock_video_placement[index + 1]["atTime"]
                        else:
                            next_time = self.duration

                        if "stock_image" in stock_video:
                            image_path = f"./temp/{video_id}/image_{image_index}.jpg"
                            if os.path.exists(image_path):
                                stock_clip = self.process_element(
                                    clip_element,
                                    {"video_clip": ImageClip(image_path, duration=30)},
                                )
                                stock_clip = add_zoom_effect(
                                    stock_clip,
                                    0,
                                    4,
                                    "out",  # np.random.choice(["in", "out"]),
                                    1.5,
                                )
                            image_index = image_index + 1

                        if "stock_video" in stock_video:
                            video_path = f"./temp/{video_id}/{video_index}.mp4"
                            # Check if video file exists first
                            if os.path.exists(video_path):
                                stock_clip = self.process_element(
                                    clip_element,
                                    {"video_clip": VideoFileClip(video_path)},
                                )
                            video_index = video_index + 1

                        if (
                            next_time
                            < (stock_clip.duration - video_start_time) + start_time
                        ):
                            end_time = next_time
                        else:
                            end_time = (
                                stock_clip.duration - video_start_time
                            ) + start_time

                        stock_clip = (
                            stock_clip.subclip(video_start_time, end_time - start_time)
                            .set_audio(None)
                            .set_start(start_time + intro_time)
                        )

                        stock_clip = add_slow_fades(stock_clip)

                        main_section_clips.append(stock_clip)

                print("stock clip ", 675)

                if main_clip:
                    # Add main content
                    main_clip = main_clip.set_start(current_time)
                    main_section_clips.append(main_clip)

                # Process logo if exists
                if logo:
                    logo_element = next(
                        (e for e in self.template["elements"] if e["id"] == "logo"),
                        None,
                    )
                    if logo_element:
                        logo_clip = self.process_element(
                            logo_element, {"source_path": logo}
                        )
                        logo_clip = logo_clip.set_start(current_time)
                        main_section_clips.append(logo_clip)

                # Add all main section clips
                all_clips.extend(main_section_clips)
                current_time += self.duration

            print("logo clip ", 700)

            # 3. Process outro clip
            if outro_clip:
                outro_clip = outro_clip.resize((self.width, self.height))
                outro_clip = outro_clip.set_start(
                    current_time
                )  # Start after main content
                all_clips.append(outro_clip)

            print("outro clip ", 710)

            # Create final composite with explicit timing
            final = CompositeVideoClip(all_clips, size=(self.width, self.height))

            if not main_clip:
                final = final.set_audio(main_audio_clip)

            print("outro clip ", 717)

            fps = 30
            final_duration = final.duration
            # Write output
            final.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                fps=fps,
                logger=ProgressLogger(video_id, "user_id"),
                remove_temp=True,
            )
            final.close()

            return final_duration

        except Exception as e:
            print(f"Error generating video: {str(e)}")
            raise e
        finally:
            # Clean up all clips
            for clip in all_clips:
                try:
                    clip.close()
                except:
                    pass
            if self.main_clip:
                try:
                    self.main_clip.close()
                except:
                    pass

    def close(self):
        """Clean up resources"""
        if hasattr(self, "background_clip"):
            self.background_clip.close()
        if hasattr(self, "main_clip"):
            self.main_clip.close()
