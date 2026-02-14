import re
from urllib.parse import urlparse


def is_youtube_url(query: str) -> bool:
    if not query.startswith(("http://", "https://")):
        return False
    parsed = urlparse(query)
    host = parsed.hostname or ""
    return any(domain in host for domain in ("youtube.com", "youtu.be", "youtube-nocookie.com"))


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", "_", name)
    name = name.strip("_.")
    return name[:200]
