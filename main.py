import yaml
from reddit_downloader import download_reddit_videos
from video_editor import create_compilation


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    print("Konfiguration geladen.")
    video_paths = download_reddit_videos(config)
    print(f"{len(video_paths)} Videos heruntergeladen.")
    create_compilation(video_paths, config)
    print("Fertiges Video erstellt!")

if __name__ == "__main__":
    main() 