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
    
    # Position setzen - versuche verschiedene Methoden
    try:
        title_clip = title_clip.with_position(('center', 0))
    except AttributeError:
        try:
            title_clip = title_clip.set_position(('center', 0))
        except AttributeError:
            print("Warnung: Kann Position für Titel nicht setzen")

    for idx, path in enumerate(video_paths):
        try:
            # MoviePy 2.x kompatible Methode zum Zuschneiden
            video_clip = VideoFileClip(path)
            
            # Versuche verschiedene Methoden zum Zuschneiden
            try:
                # Methode 1: with_subclip (MoviePy 2.x)
                duration = min(clip_length, video_clip.duration)
                clip = video_clip.with_subclip(0, duration)
            except AttributeError:
                try:
                    # Methode 2: subclip (ältere MoviePy Versionen)
                    duration = min(clip_length, video_clip.duration)
                    clip = video_clip.subclip(0, duration)
                except AttributeError:
                    # Methode 3: Kein Zuschneiden, verwende den ganzen Clip
                    print(f"Warnung: Kann Clip {path} nicht zuschneiden, verwende den ganzen Clip")
                    clip = video_clip
            
            # Hochformat erzwingen - versuche verschiedene Methoden
            try:
                clip = clip.with_size(height=height)
            except AttributeError:
                try:
                    clip = clip.resize(height=height)
                except AttributeError:
                    print(f"Warnung: Kann Clip {path} nicht in Größe ändern")
            
            # Crop falls nötig - versuche verschiedene Methoden
            if hasattr(clip, 'w') and clip.w != width:
                try:
                    clip = clip.with_crop(x_center=clip.w/2, width=width)
                except AttributeError:
                    try:
                        clip = clip.crop(x_center=clip.w/2, width=width)
                    except AttributeError:
                        print(f"Warnung: Kann Clip {path} nicht croppen")
            
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
            
            # Position setzen - versuche verschiedene Methoden
            try:
                rank_clip = rank_clip.with_position((30, 30))
            except AttributeError:
                try:
                    rank_clip = rank_clip.set_position((30, 30))
                except AttributeError:
                    print(f"Warnung: Kann Position für Ranking {idx+1} nicht setzen")
            
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
            music = AudioFileClip(music_path)
            # Duration setzen - versuche verschiedene Methoden
            try:
                music = music.with_duration(final.duration)
            except AttributeError:
                try:
                    music = music.set_duration(final.duration)
                except AttributeError:
                    print("Warnung: Kann Musik-Dauer nicht setzen")
            
            # Volume setzen - versuche verschiedene Methoden
            try:
                music = music.with_volume(0.2)
            except AttributeError:
                try:
                    music = music.volumex(0.2)
                except AttributeError:
                    print("Warnung: Kann Musik-Volume nicht setzen")
            
            # Audio setzen - versuche verschiedene Methoden
            try:
                final = final.with_audio(music)
            except AttributeError:
                try:
                    final = final.set_audio(music)
                except AttributeError:
                    print("Warnung: Kann Audio nicht setzen")
                    
        except Exception as e:
            print(f"Fehler beim Hinzufügen der Musik: {e}")

    # Exportieren
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    print(f"Exportiere fertiges Video nach {output_file}...")
    final.write_videofile(output_file, fps=30, codec='libx264', audio_codec='aac')
    print("Video erfolgreich exportiert!")
    
    # Cleanup
    final.close()
    for clip in clips:
        clip.close()
    title_clip.close() 