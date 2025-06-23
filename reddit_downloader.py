import os
import praw
import subprocess
import re

def clean_filename(title):
    # Entferne Emojis und unerlaubte Zeichen
    title = re.sub(r'[\U00010000-\U0010ffff]', '', title)  # Emojis
    title = re.sub(r'[^\w\-_ ]', '', title)  # Nur Buchstaben, Zahlen, Unterstrich, Bindestrich, Leerzeichen
    title = title.strip().replace(' ', '_')
    return title[:50]  # Maximal 50 Zeichen

def download_reddit_videos(config):
    reddit = praw.Reddit(
        client_id=config['reddit_client_id'],
        client_secret=config['reddit_client_secret'],
        user_agent=config['reddit_user_agent']
    )
    subreddit = reddit.subreddit(config['subreddit'])
    sort = config.get('reddit_sort', 'top')
    time_filter = config.get('reddit_time_filter', 'week')
    limit = config.get('reddit_limit', 20)
    number_of_clips = config.get('number_of_clips', 6)

    if not os.path.exists('videos'):
        os.makedirs('videos')

    print(f"Suche {limit} Posts aus r/{config['subreddit']}...")
    if sort == 'top':
        posts = subreddit.top(time_filter=time_filter, limit=limit)
    elif sort == 'hot':
        posts = subreddit.hot(limit=limit)
    elif sort == 'new':
        posts = subreddit.new(limit=limit)
    else:
        posts = subreddit.top(time_filter=time_filter, limit=limit)

    video_paths = []
    count = 0
    for post in posts:
        if hasattr(post, 'url') and (post.url.endswith('.mp4') or 'v.redd.it' in post.url or 'youtube.com' in post.url or 'youtu.be' in post.url):
            safe_title = clean_filename(post.title)
            out_path = f"videos/{count+1}_{safe_title}.mp4"
            print(f"Lade Video: {post.url} -> {out_path}")
            try:
                subprocess.run([
                    'yt-dlp',
                    '-f', 'mp4',
                    '-o', out_path,
                    post.url
                ], check=True)
                if os.path.exists(out_path):
                    video_paths.append(out_path)
                    count += 1
                else:
                    print(f"Fehler: Datei {out_path} wurde nicht erstellt.")
            except Exception as e:
                print(f"Fehler beim Download von {post.url}: {e}")
        if count >= number_of_clips:
            break
    print(f"{len(video_paths)} Videos erfolgreich heruntergeladen.")
    return video_paths 