from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import rotate
import os


class VideoEditor:
    def __init__(self, output_width=1920, output_height=1080, fps=30):
        """
        Initialize video editor with output dimensions and frame rate
        """
        self.width = output_width
        self.height = output_height
        self.fps = fps
        self.background_color = (0, 0, 0)

    def process_clip(self, clip_data):
        """
        Process a single clip based on provided configuration
        """
        # Load asset based on type
        clip = self.load_asset(clip_data["asset"])
        if clip is None:
            return None

        # Apply basic transformations
        clip = self.apply_transformations(clip, clip_data)

        # Apply timing
        clip = clip.set_start(clip_data.get("start", 0))
        clip = clip.set_duration(clip_data.get("length", clip.duration))

        # Apply transitions
        clip = self.apply_transitions(clip, clip_data.get("transition", {}))

        return clip

    def load_asset(self, asset_data):
        """
        Load media asset based on type
        """
        asset_type = asset_data.get("type", "").lower()
        src = asset_data.get("src", "")

        if not os.path.exists(src) and not src.startswith("http"):
            raise FileNotFoundError(f"Asset not found: {src}")

        try:
            if asset_type == "video":
                return VideoFileClip(src)
            elif asset_type == "image":
                return ImageClip(src)
            else:
                raise ValueError(f"Unsupported asset type: {asset_type}")
        except Exception as e:
            print(f"Error loading asset {src}: {str(e)}")
            return None

    def apply_transformations(self, clip, clip_data):
        """
        Apply size, position, and other transformations to clip
        """
        # Apply scale
        if "scale" in clip_data:
            clip = clip.resize(clip_data["scale"])

        # Apply fit
        fit = clip_data.get("fit", "none")
        if fit == "contain":
            clip = self.fit_contain(clip)
        elif fit == "cover":
            clip = self.fit_cover(clip)
        elif fit == "stretch":
            clip = clip.resize((self.width, self.height))

        # Apply position and offset
        clip = self.position_clip(clip, clip_data)

        # Apply rotation
        if "rotation" in clip_data:
            clip = rotate(clip, clip_data["rotation"])

        # Apply opacity
        if "opacity" in clip_data:
            clip = clip.set_opacity(clip_data["opacity"])

        # Apply crop if specified
        if "crop" in clip_data:
            clip = self.crop_clip(clip, clip_data["crop"])

        return clip

    def position_clip(self, clip, clip_data):
        """
        Position clip based on position and offset settings
        """
        # Calculate base position
        pos_x = self.width / 2 - clip.size[0] / 2
        pos_y = self.height / 2 - clip.size[1] / 2

        # Apply offset
        if "offset" in clip_data:
            offset = clip_data["offset"]
            pos_x += offset.get("x", 0) * self.width
            pos_y += offset.get("y", 0) * self.height

        # Set position
        return clip.set_position((pos_x, pos_y))

    def fit_contain(self, clip):
        """
        Scale clip to fit within frame while maintaining aspect ratio
        """
        aspect_ratio = clip.size[0] / clip.size[1]
        target_ratio = self.width / self.height

        if aspect_ratio > target_ratio:
            new_width = self.width
            new_height = self.width / aspect_ratio
        else:
            new_height = self.height
            new_width = self.height * aspect_ratio

        return clip.resize((new_width, new_height))

    def fit_cover(self, clip):
        """
        Scale clip to cover frame while maintaining aspect ratio
        """
        aspect_ratio = clip.size[0] / clip.size[1]
        target_ratio = self.width / self.height

        if aspect_ratio > target_ratio:
            new_height = self.height
            new_width = self.height * aspect_ratio
        else:
            new_width = self.width
            new_height = self.width / aspect_ratio

        return clip.resize((new_width, new_height))

    def crop_clip(self, clip, crop_data):
        """
        Crop clip based on crop settings
        """
        w, h = clip.size
        x1 = int(crop_data.get("left", 0) * w)
        y1 = int(crop_data.get("top", 0) * h)
        x2 = int(w - crop_data.get("right", 0) * w)
        y2 = int(h - crop_data.get("bottom", 0) * h)

        return clip.crop(x1=x1, y1=y1, x2=x2, y2=y2)

    def apply_transitions(self, clip, transition_data):
        """
        Apply entrance and exit transitions
        """
        if not transition_data:
            return clip

        # Apply entrance transition
        if "in" in transition_data:
            t_in = transition_data["in"]
            if isinstance(t_in, str):
                duration = 0.5  # default duration
                t_type = t_in
            else:
                duration = t_in.get("duration", 0.5)
                t_type = t_in.get("type", "fade")

            if t_type == "fade":
                clip = clip.fadein(duration)

        # Apply exit transition
        if "out" in transition_data:
            t_out = transition_data["out"]
            if isinstance(t_out, str):
                duration = 0.5  # default duration
                t_type = t_out
            else:
                duration = t_out.get("duration", 0.5)
                t_type = t_out.get("type", "fade")

            if t_type == "fade":
                clip = clip.fadeout(duration)

        return clip

    def create_video(self, composition_data):
        """
        Create final video from composition data
        """
        # Create background
        background = ColorClip(
            (self.width, self.height),
            color=self.background_color,
            duration=max(
                clip["start"] + clip["length"] for clip in composition_data["clips"]
            ),
        )

        # Process all clips
        processed_clips = []
        for clip_data in composition_data["clips"]:
            processed_clip = self.process_clip(clip_data)
            if processed_clip is not None:
                processed_clips.append(processed_clip)

        # Combine all clips
        final_video = CompositeVideoClip([background] + processed_clips)
        return final_video

    def export(self, composition_data, output_path, codec="libx264", audio_codec="aac"):
        """
        Export the final video to file
        """
        final_video = self.create_video(composition_data)
        final_video.write_videofile(
            output_path, fps=self.fps, codec=codec, audio_codec=audio_codec
        )
