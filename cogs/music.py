from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from services.downloader import download_and_convert
from services.player import get_player

log = logging.getLogger(__name__)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="join", description="Join your voice channel")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You must be in a voice channel.", ephemeral=True)
            return
        player = get_player(interaction.guild_id)
        try:
            await player.connect(interaction.user.voice.channel)
            await interaction.response.send_message(f"Joined **{interaction.user.voice.channel.name}**.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to join: {e}", ephemeral=True)

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        player = get_player(interaction.guild_id)
        if not player.voice_client or not player.voice_client.is_connected():
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
            return
        player.stop()
        await player.disconnect()
        await interaction.response.send_message("Left the voice channel.")

    @app_commands.command(name="play", description="Play a song from YouTube URL or search query")
    @app_commands.describe(query="YouTube URL or artist/song name to search")
    async def play(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You must be in a voice channel.", ephemeral=True)
            return

        await interaction.response.defer()

        player = get_player(interaction.guild_id)
        player.text_channel = interaction.channel

        try:
            await player.connect(interaction.user.voice.channel)
        except Exception as e:
            await interaction.followup.send(f"Failed to connect to voice channel: {e}")
            return

        try:
            track = await self.bot.loop.run_in_executor(None, download_and_convert, query)
        except Exception as e:
            await interaction.followup.send(f"Download failed: {e}")
            return

        position = player.add_track(track)

        if not player.is_playing:
            await player.play_track(position)
            await interaction.followup.send(f"Now playing: **{track.title}** by {track.artist}")
        else:
            await interaction.followup.send(
                f"Added to queue (#{position + 1}): **{track.title}** by {track.artist}"
            )

    @app_commands.command(name="pause", description="Pause the current track")
    async def pause(self, interaction: discord.Interaction):
        player = get_player(interaction.guild_id)
        if not player.is_playing:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return
        player.pause()
        await interaction.response.send_message("Paused.")

    @app_commands.command(name="resume", description="Resume playback")
    async def resume(self, interaction: discord.Interaction):
        player = get_player(interaction.guild_id)
        if not player.voice_client or not player.voice_client.is_paused():
            await interaction.response.send_message("Nothing is paused.", ephemeral=True)
            return
        player.resume()
        await interaction.response.send_message("Resumed.")

    @app_commands.command(name="stop", description="Stop playback and clear queue")
    async def stop(self, interaction: discord.Interaction):
        player = get_player(interaction.guild_id)
        player.stop()
        await player.disconnect()
        await interaction.response.send_message("Stopped and cleared queue.")

    @app_commands.command(name="skip", description="Skip to next song")
    async def skip(self, interaction: discord.Interaction):
        player = get_player(interaction.guild_id)
        if await player.skip():
            track = player.current_track
            await interaction.response.send_message(f"Skipped to: **{track.title}** by {track.artist}")
        else:
            await interaction.response.send_message("No more songs in queue.", ephemeral=True)

    @app_commands.command(name="next", description="Skip to next song")
    async def next_track(self, interaction: discord.Interaction):
        await self.skip.callback(self, interaction)

    @app_commands.command(name="previous", description="Go to previous song")
    async def previous(self, interaction: discord.Interaction):
        player = get_player(interaction.guild_id)
        if await player.previous():
            track = player.current_track
            await interaction.response.send_message(f"Playing previous: **{track.title}** by {track.artist}")
        else:
            await interaction.response.send_message("Already at the first song.", ephemeral=True)

    @app_commands.command(name="restartplaylist", description="Restart the queue from the beginning")
    async def restart_playlist(self, interaction: discord.Interaction):
        player = get_player(interaction.guild_id)
        if await player.restart():
            track = player.current_track
            await interaction.response.send_message(f"Restarted. Now playing: **{track.title}**")
        else:
            await interaction.response.send_message("Queue is empty.", ephemeral=True)

    @app_commands.command(name="chillax", description="Auto-DJ mode: continuously play music matching a vibe")
    @app_commands.describe(prompt="Describe the vibe (e.g. 'chill jazz', 'radiohead', '90s grunge')")
    async def chillax(self, interaction: discord.Interaction, prompt: str):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You must be in a voice channel.", ephemeral=True)
            return

        await interaction.response.defer()

        player = get_player(interaction.guild_id)
        player.text_channel = interaction.channel

        try:
            await player.connect(interaction.user.voice.channel)
        except Exception as e:
            await interaction.followup.send(f"Failed to connect: {e}")
            return

        player.stop()
        player.clear_queue()
        player.start_chillax(interaction.guild_id, prompt)

        from services.recommender import get_recommender

        try:
            recommender = get_recommender()
            search_query = await self.bot.loop.run_in_executor(
                None, recommender.recommend_next, interaction.guild_id, prompt
            )
            if search_query is None:
                player.stop_chillax()
                await interaction.followup.send(
                    f"Could not find recommendations for **{prompt}**. Try a different prompt."
                )
                return

            track = await self.bot.loop.run_in_executor(
                None, download_and_convert, search_query
            )
        except Exception as e:
            player.stop_chillax()
            await interaction.followup.send(f"Chillax startup failed: {e}")
            return

        position = player.add_track(track)
        await player.play_track(position)

        await interaction.followup.send(
            f"Chillax mode activated! Vibe: **{prompt}**\n"
            f"Now playing: **{track.title}** by {track.artist}\n"
            f"Use `/stopchillax` to stop."
        )

    @app_commands.command(name="stopchillax", description="Stop chillax auto-DJ mode")
    async def stopchillax(self, interaction: discord.Interaction):
        player = get_player(interaction.guild_id)
        if not player.chillax_active:
            await interaction.response.send_message("Chillax mode is not active.", ephemeral=True)
            return

        from services.recommender import get_recommender
        get_recommender().clear_history(interaction.guild_id)
        player.stop_chillax()
        await interaction.response.send_message(
            "Chillax mode deactivated. Current song will finish but no more will be queued."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
