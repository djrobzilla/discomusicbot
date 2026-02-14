from __future__ import annotations

import json
import logging

import anthropic

from config import ANTHROPIC_API_KEY

log = logging.getLogger(__name__)


class Recommender:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self._history: dict[int, list[str]] = {}

    def get_history(self, guild_id: int) -> list[str]:
        if guild_id not in self._history:
            self._history[guild_id] = []
        return self._history[guild_id]

    def clear_history(self, guild_id: int):
        self._history.pop(guild_id, None)

    def recommend_next(self, guild_id: int, prompt: str) -> str | None:
        history = self.get_history(guild_id)

        history_text = ""
        if history:
            recent = history[-15:]
            history_text = f"\n\nAlready played (do NOT repeat these):\n" + "\n".join(f"- {s}" for s in recent)

        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a music DJ. Given the vibe/prompt below, suggest exactly ONE song to play next. "
                    f"Return ONLY the artist and song name in the format: Artist - Song Title\n"
                    f"No explanation, no quotes, no numbering. Just the artist and song.\n\n"
                    f"Vibe/prompt: {prompt}"
                    f"{history_text}"
                ),
            }],
        )

        suggestion = message.content[0].text.strip()
        if not suggestion or len(suggestion) > 200:
            log.warning("Bad suggestion from Claude: %s", suggestion)
            return None

        log.info("Chillax recommending: %s", suggestion)
        history.append(suggestion)
        return suggestion


_recommender: Recommender | None = None


def get_recommender() -> Recommender:
    global _recommender
    if _recommender is None:
        _recommender = Recommender()
    return _recommender
