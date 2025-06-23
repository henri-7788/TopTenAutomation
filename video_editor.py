import os
from moviepy import (
    VideoFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
    AudioFileClip,
    ImageClip,
)
from PIL import ImageFont, ImageDraw, Image
import numpy as np


def _pillow_text_clip(text, font_path, fontsize, color, bg_color=None, size=None, duration=2):
    """Create a TextClip using Pillow instead of ImageMagick."""
    font = ImageFont.truetype(font_path, fontsize)
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.multiline_textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    width = size[0] if size else text_w
    height = size[1] if size and size[1] is not None else text_h
    img = Image.new("RGBA", (width, height), bg_color or (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.multiline_text(
        ((width - text_w) // 2, (height - text_h) // 2),
        text,
        font=font,
        fill=color,
        align="center",
    )
    return ImageClip(np.array(img)).set_duration(duration)

def create_compilation(video_paths, config):
    clips = []
    width, height = map(int, config['video_resolution'].split('x'))
    font_path = config['font']
    title = config['title']
    ranking_colors = config['overlay']['ranking_colors']
    title_color = config['overlay']['title_color']
    title_bg_color = config['overlay']['title_bg_color']
    text_shadow = config['overlay'].get('text_shadow', True)
    music_path = config.get('music', None)
    output_file = config['output_file']
    clip_length = config.get('clip_length_seconds', 30)

    # Titel-Overlay vorbereiten (ohne ImageMagick)
    title_clip = _pillow_text_clip(
        title,
        font_path,
        70,
        title_color,
        bg_color=title_bg_color,
        size=(width, None),
        duration=2,
    ).set_position(('center', 0))

    for idx, path in enumerate(video_paths):
        try:
            clip = VideoFileClip(path).subclip(0, min(clip_length, VideoFileClip(path).duration))
            # Hochformat erzwingen
            clip = clip.resize(height=height)
            if clip.w != width:
                clip = clip.crop(x_center=clip.w/2, width=width)
            # Ranking-Overlay
            rank_text = f"{idx+1}."
            rank_clip = _pillow_text_clip(
                rank_text,
                font_path,
                60,
                ranking_colors[idx] if idx < len(ranking_colors) else '#FFFFFF',
                bg_color=None,
                duration=clip.duration,
            ).set_position((30, 30))
            # Kombiniere Clip und Overlay
            composite = CompositeVideoClip([clip, rank_clip])
            clips.append(composite)
        except Exception as e:
            print(f"Fehler beim Verarbeiten von {path}: {e}")

    # Alle Clips zusammenfügen
    final = concatenate_videoclips([title_clip] + clips, method="compose")

    # Musik hinzufügen
    if music_path and os.path.exists(music_path):
        try:
            music = AudioFileClip(music_path).volumex(0.2)
            final = final.set_audio(music.set_duration(final.duration))
        except Exception as e:
            print(f"Fehler beim Hinzufügen der Musik: {e}")

    # Exportieren
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    print(f"Exportiere fertiges Video nach {output_file}...")
    final.write_videofile(output_file, fps=30, codec='libx264', audio_codec='aac')
    print("Video erfolgreich exportiert!") 