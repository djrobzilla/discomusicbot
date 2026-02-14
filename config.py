import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

BASE_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = BASE_DIR / "videos"
MP3S_DIR = BASE_DIR / "mp3s"
PLAYLISTS_DIR = BASE_DIR / "playlists"

VIDEOS_DIR.mkdir(exist_ok=True)
MP3S_DIR.mkdir(exist_ok=True)
PLAYLISTS_DIR.mkdir(exist_ok=True)
