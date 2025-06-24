import os
import sys
import logging
import praw
import subprocess
import re
import yaml

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Lade Konfiguration
def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

CLIENT_ID = config["reddit_client_id"]
CLIENT_SECRET = config["reddit_client_secret"]
USER_AGENT = config["reddit_user_agent"]
SUBREDDIT_NAME = config["subreddit"]
TIME_FILTER = config.get("reddit_time_filter", "week")
DOWNLOAD_DIR = "videos"
DOWNLOADED_IDS_FILE = os.path.join(DOWNLOAD_DIR, "downloaded_ids.txt")

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
if not os.path.exists(DOWNLOADED_IDS_FILE):
    with open(DOWNLOADED_IDS_FILE, "w") as f:
        pass

def load_downloaded_ids():
    with open(DOWNLOADED_IDS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_downloaded_id(post_id):
    with open(DOWNLOADED_IDS_FILE, "a") as f:
        f.write(post_id + "\n")

def save_caption(post):
    caption = post.title
    caption_file = os.path.join(DOWNLOAD_DIR, f"{post.id}.txt")
    try:
        with open(caption_file, "w", encoding="utf-8") as f:
            f.write(caption)
        logging.info(f"Caption für Post {post.id} wurde in {caption_file} gespeichert.")
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Caption für Post {post.id}: {e}")

def clean_filename(title):
    # Entferne Emojis und unerlaubte Zeichen
    title = re.sub(r'[\U00010000-\U0010ffff]', '', title)  # Emojis
    title = re.sub(r'[^\w\-_ ]', '', title)  # Nur Buchstaben, Zahlen, Unterstrich, Bindestrich, Leerzeichen
    title = title.strip().replace(' ', '_')
    return title[:50]  # Maximal 50 Zeichen

# Initialisiere Reddit API via PRAW
reddit = praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     user_agent=USER_AGENT)

def get_ytdlp_cmd():
    base = os.path.dirname(__file__)
    if sys.platform.startswith('win'):
        exe = os.path.join(base, 'tools', 'yt-dlp', 'windows', 'yt-dlp.exe')
        if os.path.isfile(exe):
            return exe
        else:
            return 'yt-dlp.exe'
    else:
        exe = os.path.join(base, 'tools', 'yt-dlp', 'linux', 'yt-dlp_linux')
        if os.path.isfile(exe):
            return exe
        else:
            return 'yt-dlp'

def download_video(url, output_path):
    try:
        subprocess.run([
            get_ytdlp_cmd(),
            '-f', 'bv*+ba/best',
            '--merge-output-format', 'mp4',
            '-o', output_path,
            url
        ], check=True)
        return os.path.exists(output_path)
    except Exception as e:
        logging.error(f"Fehler beim Herunterladen von {url}: {e}")
        return False

def process_post(post):
    downloaded_ids = load_downloaded_ids()
    if post.id in downloaded_ids:
        logging.info(f"Post {post.id} wurde bereits gerippt.")
        return False

    video_url = None
    filename = None

    # Prüfe, ob es sich um ein unterstütztes Video handelt
    if hasattr(post, 'url') and (post.url.endswith('.mp4') or 'v.redd.it' in post.url or 'youtube.com' in post.url or 'youtu.be' in post.url):
        video_url = post.url
        safe_title = clean_filename(post.title)
        filename = f"{post.id}_{safe_title}.mp4"
    elif post.is_video and post.media and "reddit_video" in post.media:
        video_url = post.media["reddit_video"].get("fallback_url")
        safe_title = clean_filename(post.title)
        filename = f"{post.id}_{safe_title}.mp4"
    else:
        logging.info(f"Post {post.id} enthält kein unterstütztes Video.")
        return False

    file_path = os.path.join(DOWNLOAD_DIR, filename)
    logging.info(f"Lade {post.id} von {video_url} herunter...")

    if not download_video(video_url, file_path):
        logging.error(f"Download von {post.id} fehlgeschlagen.")
        return False

    logging.info(f"Post {post.id} wurde erfolgreich heruntergeladen.")
    save_caption(post)
    save_downloaded_id(post.id)
    return True

def download_top_videos(config, top_n=6):
    subreddit = reddit.subreddit(config["subreddit"])
    time_filter = config.get("reddit_time_filter", "week")
    limit = config.get("reddit_limit", 20)
    video_paths = []
    count = 0
    logging.info(f"Lade die Top {top_n} Videos aus r/{config['subreddit']} (Timefilter: {time_filter})")
    for post in subreddit.top(time_filter=time_filter, limit=limit):
        if count >= top_n:
            break
        if process_post(post):
            safe_title = clean_filename(post.title)
            filename = f"{post.id}_{safe_title}.mp4"
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.exists(file_path):
                video_paths.append(file_path)
                count += 1
    logging.info(f"{len(video_paths)} Videos erfolgreich heruntergeladen.")
    return video_paths

def main():
    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    logging.info(f"Verarbeite Top-Posts aus r/{SUBREDDIT_NAME} (Timefilter: {TIME_FILTER})")
    for post in subreddit.top(time_filter=TIME_FILTER, limit=50):
        if process_post(post):
            logging.info("Erfolgreich ein Video heruntergeladen. Beende das Skript.")
            break

if __name__ == "__main__":
    main() 