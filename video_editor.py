import os
from moviepy import VideoFileClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.VideoClip import TextClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

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

    # Titel-Overlay vorbereiten
    title_clip = TextClip(
        text=title,
        font=font_path,
        font_size=70,
        color=title_color,
        bg_color=title_bg_color,
        size=(width, None),
        method='caption',
        duration=2
    )
    title_clip = title_clip.with_position(('center', 0))

    for idx, path in enumerate(video_paths):
        try:
            clip = VideoFileClip(path).subclip(0, min(clip_length, VideoFileClip(path).duration))
            # Hochformat erzwingen
            clip = clip.with_size(height=height)
            if clip.w != width:
                clip = clip.with_crop(x_center=clip.w/2, width=width)
            # Ranking-Overlay
            rank_text = f"{idx+1}."
            rank_clip = TextClip(
                text=rank_text,
                font=font_path,
                font_size=60,
                color=ranking_colors[idx] if idx < len(ranking_colors) else '#FFFFFF',
                method='caption',
                duration=clip.duration
            )
            rank_clip = rank_clip.with_position((30, 30))
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
            music = AudioFileClip(music_path).with_duration(final.duration).with_volume(0.2)
            final = final.with_audio(music)
        except Exception as e:
            print(f"Fehler beim Hinzufügen der Musik: {e}")

    # Exportieren
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    print(f"Exportiere fertiges Video nach {output_file}...")
    final.write_videofile(output_file, fps=30, codec='libx264', audio_codec='aac')
    print("Video erfolgreich exportiert!") 