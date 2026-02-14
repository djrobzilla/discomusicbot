from __future__ import annotations

import json
import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config import PLAYLISTS_DIR
from services.downloader import Track, download_and_convert
from services.player import get_player
from utils.helpers import sanitize_filename

log = logging.getLogger(__name__)

# In-memory playlist storage: {name: [Track, ...]}
_playlists: dict[str, list[Track]] = {}


def _playlist_path(name: str) -> Path:
    return PLAYLISTS_DIR / f"{sanitize_filename(name)}.json"


def _save_playlist(name: str):
    data = {
        "name": name,
        "tracks": [t.to_dict() for t in _playlists.get(name, [])],
    }
    _playlist_path(name).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_playlist(name: str) -> list[Track] | None:
    path = _playlist_path(name)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Track.from_dict(t) for t in data.get("tracks", [])]


class Playlists(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="createplaylist", description="Create a new empty playlist")
    @app_commands.describe(name="Playlist name")
    async def create_playlist(self, interaction: discord.Interaction, name: str):
        if name in _playlists:
            await interaction.response.send_message(f"Playlist **{name}** already exists.", ephemeral=True)
            return
        _playlists[name] = []
        await interaction.response.send_message(f"Created playlist: **{name}**")

    @app_commands.command(name="addtoplaylist", description="Add a song to a playlist")
    @app_commands.describe(name="Playlist name", query="YouTube URL or search query")
    async def add_to_playlist(self, interaction: discord.Interaction, name: str, query: str):
        if name not in _playlists:
            await interaction.response.send_message(f"Playlist **{name}** not found. Create it first.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            track = await self.bot.loop.run_in_executor(None, download_and_convert, query)
        except Exception as e:
            await interaction.followup.send(f"Failed to add track: {e}")
            return

        _playlists[name].append(track)
        await interaction.followup.send(
            f"Added **{track.title}** to playlist **{name}** (#{len(_playlists[name])})"
        )

    @app_commands.command(name="removefromplaylist", description="Remove a song from a playlist by index")
    @app_commands.describe(name="Playlist name", index="Track number (starting from 1)")
    async def remove_from_playlist(self, interaction: discord.Interaction, name: str, index: int):
        if name not in _playlists:
            await interaction.response.send_message(f"Playlist **{name}** not found.", ephemeral=True)
            return

        tracks = _playlists[name]
        idx = index - 1
        if idx < 0 or idx >= len(tracks):
            await interaction.response.send_message(
                f"Invalid index. Playlist has {len(tracks)} track(s).", ephemeral=True
            )
            return

        removed = tracks.pop(idx)
        await interaction.response.send_message(f"Removed **{removed.title}** from **{name}**.")

    @app_commands.command(name="renameplaylist", description="Rename a playlist")
    @app_commands.describe(old="Current name", new="New name")
    async def rename_playlist(self, interaction: discord.Interaction, old: str, new: str):
        if old not in _playlists:
            await interaction.response.send_message(f"Playlist **{old}** not found.", ephemeral=True)
            return
        if new in _playlists:
            await interaction.response.send_message(f"Playlist **{new}** already exists.", ephemeral=True)
            return

        _playlists[new] = _playlists.pop(old)

        old_path = _playlist_path(old)
        if old_path.exists():
            old_path.unlink()

        await interaction.response.send_message(f"Renamed **{old}** to **{new}**.")

    @app_commands.command(name="saveplaylists", description="Save all playlists to disk")
    async def save_playlists(self, interaction: discord.Interaction):
        for name in _playlists:
            _save_playlist(name)
        await interaction.response.send_message(f"Saved {len(_playlists)} playlist(s) to disk.")

    @app_commands.command(name="listplaylists", description="List all saved playlists")
    async def list_playlists(self, interaction: discord.Interaction):
        on_disk = [p.stem for p in PLAYLISTS_DIR.glob("*.json")]
        in_memory = list(_playlists.keys())
        all_names = sorted(set(on_disk + in_memory))

        if not all_names:
            await interaction.response.send_message("No playlists found.")
            return

        lines = []
        for name in all_names:
            count = len(_playlists[name]) if name in _playlists else "?"
            lines.append(f"- **{name}** ({count} tracks)")

        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="loadplaylist", description="Load a saved playlist and start playing")
    @app_commands.describe(name="Playlist name")
    async def load_playlist(self, interaction: discord.Interaction, name: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You must be in a voice channel.", ephemeral=True)
            return

        tracks = _playlists.get(name)
        if tracks is None:
            tracks = _load_playlist(name)
            if tracks is None:
                await interaction.response.send_message(f"Playlist **{name}** not found.", ephemeral=True)
                return
            _playlists[name] = tracks

        if not tracks:
            await interaction.response.send_message(f"Playlist **{name}** is empty.", ephemeral=True)
            return

        await interaction.response.defer()

        player = get_player(interaction.guild_id)
        player.text_channel = interaction.channel

        try:
            await player.connect(interaction.user.voice.channel)
        except Exception as e:
            await interaction.followup.send(f"Failed to connect: {e}")
            return

        player.clear_queue()
        for track in tracks:
            player.add_track(track)

        await player.play_track(0)
        await interaction.followup.send(
            f"Loaded playlist **{name}** ({len(tracks)} tracks). Now playing: **{tracks[0].title}**"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Playlists(bot))
