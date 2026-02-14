from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord

from services.downloader import Track

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


class Player:
    def __init__(self):
        self.queue: list[Track] = []
        self.current_index: int = -1
        self.voice_client: discord.VoiceClient | None = None
        self.text_channel: discord.abc.Messageable | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

        # Chillax mode state
        self.chillax_active: bool = False
        self.chillax_prompt: str = ""
        self.chillax_guild_id: int | None = None
        self._chillax_loading: bool = False

    @property
    def current_track(self) -> Track | None:
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    @property
    def is_playing(self) -> bool:
        return self.voice_client is not None and self.voice_client.is_playing()

    def add_track(self, track: Track) -> int:
        self.queue.append(track)
        return len(self.queue) - 1

    def clear_queue(self):
        self.queue.clear()
        self.current_index = -1

    async def connect(self, channel: discord.VoiceChannel) -> discord.VoiceClient:
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel.id != channel.id:
                await self.voice_client.move_to(channel)
            return self.voice_client

        self.voice_client = await channel.connect()
        return self.voice_client

    async def disconnect(self):
        if self.voice_client and self.voice_client.is_connected():
            await self.voice_client.disconnect()
        self.voice_client = None

    async def play_track(self, index: int | None = None):
        if index is not None:
            self.current_index = index
        elif self.current_index == -1:
            self.current_index = 0

        track = self.current_track
        if not track or not self.voice_client:
            return

        if self.voice_client.is_playing():
            self.voice_client.stop()

        source = discord.FFmpegOpusAudio(track.mp3_path)
        self._loop = asyncio.get_running_loop()
        self.voice_client.play(source, after=self._after_playback)
        log.info("Now playing: %s", track.title)

        if self.text_channel:
            asyncio.run_coroutine_threadsafe(
                self.text_channel.send(f"Now playing: **{track.title}** by {track.artist}"),
                self._loop,
            )

    def start_chillax(self, guild_id: int, prompt: str):
        self.chillax_active = True
        self.chillax_prompt = prompt
        self.chillax_guild_id = guild_id
        self._chillax_loading = False

    def stop_chillax(self):
        self.chillax_active = False
        self.chillax_prompt = ""
        self._chillax_loading = False

    def _after_playback(self, error: Exception | None):
        if error:
            log.error("Playback error: %s", error)
            return

        if self.current_index + 1 < len(self.queue):
            self.current_index += 1
            if self._loop:
                asyncio.run_coroutine_threadsafe(self.play_track(), self._loop)
            return

        if self.chillax_active and self._loop and not self._chillax_loading:
            self._chillax_loading = True
            asyncio.run_coroutine_threadsafe(self._chillax_next(), self._loop)

    async def _chillax_next(self):
        from services.recommender import get_recommender
        from services.downloader import download_and_convert

        try:
            recommender = get_recommender()
            loop = asyncio.get_running_loop()

            search_query = await loop.run_in_executor(
                None, recommender.recommend_next, self.chillax_guild_id, self.chillax_prompt
            )

            if search_query is None:
                if self.text_channel:
                    await self.text_channel.send(
                        "Chillax mode: Could not find more recommendations. Stopping."
                    )
                self.stop_chillax()
                return

            track = await loop.run_in_executor(None, download_and_convert, search_query)

            position = self.add_track(track)
            await self.play_track(position)

        except Exception as e:
            log.error("Chillax next track failed: %s", e)
            if self.text_channel:
                await self.text_channel.send("Chillax mode: Error fetching next track. Retrying...")
            await asyncio.sleep(3)
            self._chillax_loading = False
            if self.chillax_active:
                await self._chillax_next()
        finally:
            self._chillax_loading = False

    async def skip(self):
        if self.current_index + 1 < len(self.queue):
            self.current_index += 1
            await self.play_track()
            return True
        return False

    async def previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            await self.play_track()
            return True
        return False

    async def restart(self):
        if self.queue:
            self.current_index = 0
            await self.play_track()
            return True
        return False

    def pause(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()

    def resume(self):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()

    def stop(self):
        if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
            self.voice_client.stop()
        self.stop_chillax()
        self.clear_queue()


# Per-guild player instances
_players: dict[int, Player] = {}


def get_player(guild_id: int) -> Player:
    if guild_id not in _players:
        _players[guild_id] = Player()
    return _players[guild_id]
