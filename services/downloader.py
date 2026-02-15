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


def _build_audio_filename(artist: str, album: str | None, title: str) -> str:
    if album:
        name = f"{artist} - {album} - {title}"
    else:
        name = f"{artist} - {title}"
    return sanitize_filename(name) + ".opus"


def _find_cached_audio(video_id: str, pretty_name: str) -> Path | None:
    pretty_path = MP3S_DIR / pretty_name
    if pretty_path.exists():
        return pretty_path
    # Check legacy formats
    for ext in (".opus", ".mp3"):
        legacy_path = MP3S_DIR / f"{video_id}{ext}"
        if legacy_path.exists():
            return legacy_path
    return None


def download_and_convert(query: str) -> Track:
    if is_youtube_url(query):
        search_query = query
    else:
        search_query = f"ytsearch1:{query}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(MP3S_DIR / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "opus",
            "preferredquality": "128",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        if "entries" in info:
            if not info["entries"]:
                raise ValueError(f"No results found for: {query}")
            info = info["entries"][0]

        video_id = info["id"]
        title = info.get("title", "Unknown")
        artist = info.get("artist") or info.get("uploader") or "Unknown"
        album = info.get("album") or None
        url = info.get("webpage_url", query)
        duration = info.get("duration", 0)

        pretty_name = _build_audio_filename(artist, album, title)
        cached = _find_cached_audio(video_id, pretty_name)
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl_dl:
            ydl_dl.download([url])

        # Rename from video_id.opus to pretty name
        raw_path = MP3S_DIR / f"{video_id}.opus"
        pretty_path = MP3S_DIR / pretty_name
        if raw_path.exists():
            raw_path.rename(pretty_path)
            mp3_path = pretty_path
        else:
            mp3_path = raw_path

        return Track(
            title=title,
            artist=artist,
            url=url,
            video_id=video_id,
            mp3_path=str(mp3_path),
            duration=duration,
        )
