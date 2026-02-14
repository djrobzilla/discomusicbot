from __future__ import annotations

import logging
from dataclasses import dataclass, asdict
from pathlib import Path

import yt_dlp

from config import MP3S_DIR, VIDEOS_DIR
from utils.helpers import is_youtube_url, sanitize_filename

log = logging.getLogger(__name__)


@dataclass
class Track:
    title: str
    artist: str
    url: str
    video_id: str
    mp3_path: str
    duration: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Track:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def _cached_mp3(video_id: str) -> Path | None:
    path = MP3S_DIR / f"{video_id}.mp3"
    return path if path.exists() else None


def download_and_convert(query: str) -> Track:
    if is_youtube_url(query):
        search_query = query
    else:
        search_query = f"ytsearch1:{query}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(VIDEOS_DIR / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        if "entries" in info:
            info = info["entries"][0]

        video_id = info["id"]
        title = info.get("title", "Unknown")
        artist = info.get("artist") or info.get("uploader") or "Unknown"
        url = info.get("webpage_url", query)
        duration = info.get("duration", 0)

        cached = _cached_mp3(video_id)
        if cached:
            log.info("Cache hit for %s", video_id)
            return Track(
                title=title,
                artist=artist,
                url=url,
                video_id=video_id,
                mp3_path=str(cached),
                duration=duration,
            )

        log.info("Downloading %s", video_id)
        ydl_opts["outtmpl"] = str(MP3S_DIR / "%(id)s.%(ext)s")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl_dl:
            ydl_dl.download([url])

        mp3_path = MP3S_DIR / f"{video_id}.mp3"
        return Track(
            title=title,
            artist=artist,
            url=url,
            video_id=video_id,
            mp3_path=str(mp3_path),
            duration=duration,
        )
