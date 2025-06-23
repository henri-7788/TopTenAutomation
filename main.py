import yaml
import reddit_downloader
from video_editor import create_compilation
import os


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    print("Konfiguration geladen.")
    # Download der Top 6 Videos, gibt Liste der Videopfad zurück
    video_paths = reddit_downloader.download_top_videos(config, top_n=6)
    print(f"{len(video_paths)} Videos heruntergeladen.")
    if video_paths:
        create_compilation(video_paths, config)
        print("Fertiges Video erstellt!")
    else:
        print("Keine Videos zum Erstellen der Compilation gefunden.")

if __name__ == "__main__":
    main() 