import asyncio
import logging

import discord
from discord.ext import commands

from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

if not discord.opus.is_loaded():
    import sys
    _opus_candidates = (
        ["/usr/lib/x86_64-linux-gnu/libopus.so.0"] if sys.platform == "linux"
        else ["opus", "libopus-0", "libopus0"]
    )
    for _name in _opus_candidates:
        try:
            discord.opus.load_opus(_name)
            break
        except Exception:
            continue
    log.info("Opus loaded: %s", discord.opus.is_loaded())

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = ["cogs.music", "cogs.playlists"]
GUILD = discord.Object(id=612359079351812127)


@bot.event
async def on_ready():
    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    try:
        bot.tree.copy_global_to(guild=GUILD)
        synced = await bot.tree.sync(guild=GUILD)
        log.info("Synced %d slash command(s) to guild", len(synced))
    except Exception as e:
        log.error("Failed to sync commands: %s", e)


async def main():
    if not BOT_TOKEN:
        log.error("BOT_TOKEN not set. Copy .env.example to .env and add your token.")
        return

    async with bot:
        for cog in COGS:
            await bot.load_extension(cog)
            log.info("Loaded cog: %s", cog)
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
