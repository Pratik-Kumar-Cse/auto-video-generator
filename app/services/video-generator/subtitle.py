from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    CompositeVideoClip,
    TextClip,
)
from PIL import Image, ImageDraw
from moviepy.video.tools.subtitles import SubtitlesClip
import srt
import re
import numpy as np
from moviepy.editor import vfx
from moviepy.video.tools.drawing import color_gradient
from ..utils import download_font


def create_rounded_rectangle_masks(size, radius):
    """Create a rounded rectangle mask using PIL"""
    width, height = size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (width - 1, height - 1)], radius, fill=255)
    return np.array(mask)


def add_styled_subtitles(video_path, srt_path, output_path, style_type="default"):
    """
    Add stylized subtitles to a video from an SRT file.
    """
    video = VideoFileClip(video_path).resize((854, 480))

    def default_subtitle(txt):
        return TextClip(
            txt=txt.upper(),
            fontsize=50,
            color="white",
            font="Arial",
            method="label",
            size=video.size,
        )

    def gradient_subtitle(txt):
        gradient = color_gradient(
            video.size[0],
            50,
            color1=[255, 0, 0],
            color2=[0, 0, 255],
            shape="horizontal",
        )
        return TextClip(
            txt,
            fontsize=24,
            color="white",
            font="Arial",
            method="label",
            size=video.size,
            bg_color=gradient,
        )

    def outline_subtitle(txt):
        return TextClip(
            txt,
            fontsize=24,
            color="white",
            font="Arial",
            method="label",
            size=video.size,
            stroke_color="black",
            stroke_width=2,
        )

    def shadow_subtitle(txt):
        return TextClip(
            txt,
            fontsize=24,
            color="white",
            font="Arial",
            method="label",
            size=video.size,
            shadow_color="black",
            shadow_offset=(3, 3),
        )

    subtitle_styles = {
        "default": default_subtitle,
        "gradient": gradient_subtitle,
        "outline": outline_subtitle,
        "shadow": shadow_subtitle,
    }

    generator = SubtitlesClip(
        srt_path, subtitle_styles.get(style_type, default_subtitle)
    )
    final_video = CompositeVideoClip([video, generator.set_pos(("center", "bottom"))])
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

    video.close()
    final_video.close()


def create_styled_subtitles(
    srt_file_path,
    font="Arial",
    fontsize=24,
    color="white",
    bgcolor="black",
    line_space=4,
    duration_offset=0.2,
    animation_type="fade_in",
    animation_duration=0.5,
):
    with open(srt_file_path, "r", encoding="utf-8") as f:
        srt_content = f.read()

    subs = list(srt.parse(srt_content))
    text_clips = []

    for sub in subs:
        start_time = sub.start.total_seconds()
        end_time = sub.end.total_seconds()
        text = sub.content
        duration = end_time - start_time

        txt_clip = (
            TextClip(
                text,
                font=font,
                fontsize=fontsize,
                color=color,
                bg_color=bgcolor,
                size=(1200, None),
                method="caption",
                align="center",
            )
            .set_duration(duration)
            .set_position(("center", "bottom"))
        )

        if animation_type == "fade_in":
            txt_clip = txt_clip.fx(vfx.fadein, animation_duration).fx(
                vfx.fadeout, animation_duration
            )
        elif animation_type == "slide_in":
            txt_clip = txt_clip.set_position(
                lambda t: (
                    "center",
                    min(1080, 800 + t * 100) if t < animation_duration else "bottom",
                )
            )

        txt_clip = txt_clip.set_start(start_time).set_end(end_time)
        text_clips.append(txt_clip)

    return text_clips


def overlay_subtitles(video_path, srt_file_path, output_path, **subtitle_kwargs):
    video = VideoFileClip(video_path)
    styled_clips = create_styled_subtitles(srt_file_path, **subtitle_kwargs)
    final_clip = CompositeVideoClip([video] + styled_clips, size=video.size)
    final_clip.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=video.fps,
        threads=4,
        preset="ultrafast",
    )

    video.close()
    final_clip.close()
    for clip in styled_clips:
        clip.close()


def create_text_generator(
    font_path="./asset/font/bold_font.ttf",
    font_size=50,
    text_color="#FFFFFF",
    highlight_color="#FFFF00",
    video_width=1280,
    corner_radius=30,
):
    if font_path != "./asset/font/bold_font.ttf":
        font_path = download_font(font_path)

    def generate_subtitle(txt, highlight_word=None):
        words = txt.split()
        word_clips = []
        x_offset = 0

        for word in words:
            color = (
                highlight_color
                if highlight_word and word.lower() == highlight_word.lower()
                else text_color
            )
            word_clip = TextClip(
                txt=word.upper(),
                font=font_path,
                fontsize=font_size,
                color=color,
                stroke_color="black",
                stroke_width=2,
                method="label",
                align="center",
                transparent=True,
            )
            word_clips.append(word_clip.set_position((x_offset, 0)))
            x_offset += word_clip.w + 10

        text_composite = CompositeVideoClip(word_clips)
        padding_x, padding_y = 25, 20
        bg_width = text_composite.w + padding_x * 2
        bg_height = text_composite.h + padding_y * 2

        mask = create_rounded_rectangle_masks((bg_width, bg_height), corner_radius)
        bg_frame = np.zeros((bg_height, bg_width, 3), dtype=np.uint8)
        bg_clip = ImageClip(bg_frame)
        bg_clip.mask = ImageClip(mask, ismask=True)

        x_pos = (video_width - bg_width) // 2
        final_clip = CompositeVideoClip(
            [
                bg_clip.set_opacity(0.5),
                text_composite.set_position((padding_x, padding_y)),
            ],
            size=(bg_width, bg_height),
        )

        return final_clip.set_position((x_pos, "bottom"))

    return generate_subtitle


def parse_time(time_str):
    """Convert SRT time format to seconds"""
    hours, minutes, seconds = time_str.replace(",", ".").split(":")
    return float(hours) * 3600 + float(minutes) * 60 + float(seconds)


def create_text_generatorss(
    font_path="./asset/font/bold_font.ttf",
    font_size=50,
    current_color="#FFFF00",
    context_color="#FFFFFF",
    video_width=1280,
    corner_radius=30,
):
    if font_path != "./asset/font/bold_font.ttf":
        font_path = download_font(font_path)

    def generate_subtitle(text):
        words = text.split("|")
        if len(words) != 3:
            words = ["", text, ""]

        prev_word, current_word, next_word = words
        word_clips = []
        x_offset = 0

        words_with_colors = [
            (prev_word, context_color),
            (current_word, current_color),
            (next_word, context_color),
        ]

        for word, color in words_with_colors:
            if word.strip():
                word_clip = TextClip(
                    txt=word.upper(),
                    font=font_path,
                    fontsize=font_size,
                    color=color,
                    stroke_color="black",
                    stroke_width=2,
                    method="label",
                    align="center",
                    transparent=True,
                )
                word_clips.append(word_clip.set_position((x_offset, 0)))
                x_offset += word_clip.w + 20

        if not word_clips:
            return None

        text_composite = CompositeVideoClip(word_clips)
        padding_x, padding_y = 30, 20
        bg_width = text_composite.w + padding_x * 2
        bg_height = text_composite.h + padding_y * 2

        mask = create_rounded_rectangle_masks((bg_width, bg_height), corner_radius)
        bg_frame = np.zeros((bg_height, bg_width, 3), dtype=np.uint8)
        bg_clip = ImageClip(bg_frame)
        bg_clip.mask = ImageClip(mask, ismask=True)

        x_pos = (video_width - bg_width) // 2
        final_clip = CompositeVideoClip(
            [
                bg_clip.set_opacity(0.5),
                text_composite.set_position((padding_x, padding_y)),
            ],
            size=(bg_width, bg_height),
        )

        return final_clip.set_position((x_pos, "bottom"))

    return generate_subtitle


def process_srt_with_context(srt_file):
    """Process SRT file and create context-aware subtitle data"""
    with open(srt_file, "r") as f:
        content = f.read().strip()

    subtitle_entries = content.split("\n\n")
    all_words = []

    for entry in subtitle_entries:
        lines = entry.strip().split("\n")
        if len(lines) >= 3:
            times = lines[1].split(" --> ")
            start_time = parse_time(times[0])
            end_time = parse_time(times[1])
            text = " ".join(lines[2:]).strip()
            text = re.sub(r"\s+", " ", text)
            all_words.append((start_time, end_time, text))

    subtitle_data = []
    for i, (start_time, end_time, current_word) in enumerate(all_words):
        prev_word = all_words[i - 1][2] if i > 0 else ""
        next_word = all_words[i + 1][2] if i < len(all_words) - 1 else ""
        text_with_context = f"{prev_word}|{current_word}|{next_word}"
        subtitle_data.append(((start_time, end_time), text_with_context))

    return subtitle_data


def create_video_with_subtitles(video_path, srt_path, output_path):
    video = VideoFileClip(video_path).resize((1280, 720))
    generator = create_text_generatorss()
    subtitle_data = process_srt_with_context(srt_path)
    subtitles = SubtitlesClip(subtitle_data, generator)
    final_video = CompositeVideoClip(
        [video, subtitles.set_position(("center", "center"))]
    )
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")

    video.close()
    final_video.close()


# Example usage
video_path = "./temp/67611f6ec6faed41e9f01e5a/avatar_0.mp4"
srt_path = "./temp/67611f6ec6faed41e9f01e5a/67611f6ec6faed41e9f01e5a.srt"
output_path = "./temp/output_video_with_context.mp4"

# create_video_with_subtitles(video_path, srt_path, output_path)
