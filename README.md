# Discord Music Bot

A Python Discord bot that plays music from YouTube in voice channels. Supports URL and search-based playback, queue management, and persistent playlists.

## Features

- Play music from YouTube URLs or search queries
- Queue management with skip, previous, and restart
- Named playlists with save/load (JSON persistence)
- Audio caching (Opus format) to avoid re-downloading
- Per-guild playback (works across multiple servers)
- **Chillax mode** — AI-powered auto-DJ that continuously plays music matching a vibe (powered by Claude)
- Smart prefetching — next song is downloaded while the current one plays for gapless transitions
- `/reroll` — don't like the next pick? Reroll for a different suggestion
- Downloaded files named as `Artist - Album - Title.opus` for easy browsing
- `/silent` mode — suppress bot chat messages (responses become ephemeral)
- `/clearcache` — clear the downloaded audio file cache

## Requirements

- Python 3.10+
- FFmpeg (must be installed and in PATH)
- A Discord bot token
- An Anthropic API key (for chillax mode) — get one at [console.anthropic.com](https://console.anthropic.com)

## Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/djrobzilla/discomusicbot.git
   cd discomusicbot
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate        # Linux/macOS
   # venv\Scripts\activate          # Windows
   pip install -r requirements.txt
   ```

3. **Install FFmpeg:**
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg

   # macOS
   brew install ffmpeg

   # Windows (via winget)
   winget install ffmpeg
   ```

4. **Install libopus (Linux only):**
   ```bash
   sudo apt install libopus0
   ```

5. **Configure your bot token:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Discord bot token and Anthropic API key:
   ```
   BOT_TOKEN=your_discord_bot_token
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

6. **Run the bot:**
   ```bash
   python bot.py
   ```
   Or use the helper scripts: `./run.sh` (Linux/macOS) or `run.bat` (Windows).

## Discord Setup

1. Create an application at the [Discord Developer Portal](https://discord.com/developers/applications)
2. Under **Bot**, enable **Message Content Intent**
3. Invite the bot with the `bot` and `applications.commands` scopes, and **Connect** + **Speak** + **Send Messages** permissions

## Commands

| Command | Description |
|---------|-------------|
| `/join` | Join your voice channel |
| `/leave` | Leave the voice channel |
| `/play <url_or_query>` | Add song to queue and play |
| `/pause` | Pause playback |
| `/resume` | Resume playback |
| `/stop` | Stop playback and clear queue |
| `/skip` | Skip to next song |
| `/next` | Skip to next song |
| `/previous` | Go to previous song |
| `/chillax <prompt>` | Start AI auto-DJ matching a vibe (e.g. "chill jazz", "90s grunge") |
| `/stopchillax` | Stop chillax auto-DJ mode |
| `/reroll` | Reroll the next chillax song pick |
| `/restartplaylist` | Restart queue from beginning |
| `/silent` | Toggle silent mode (suppresses bot chat messages) |
| `/clearcache` | Clear the downloaded audio file cache |
| `/createplaylist <name>` | Create empty playlist |
| `/addtoplaylist <name> <query>` | Add song to playlist |
| `/removefromplaylist <name> <index>` | Remove song from playlist |
| `/renameplaylist <old> <new>` | Rename playlist |
| `/saveplaylists` | Save all playlists to disk |
| `/listplaylists` | List saved playlists |
| `/loadplaylist <name>` | Load and play a saved playlist |

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
