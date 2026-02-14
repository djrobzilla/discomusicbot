# Changelog

## v1.1.0 - 2026-02-14

### Added
- Chillax mode: AI-powered continuous auto-DJ (`/chillax <prompt>`, `/stopchillax`)
- Claude Haiku integration for intelligent song recommendations based on vibes, artists, or genres
- Per-guild play history tracking to avoid repeat songs in chillax mode
- New dependency: `anthropic` SDK

## v1.0.0 - 2026-02-14

### Added
- YouTube playback via URL or search query using yt-dlp
- FFmpeg MP3 conversion with caching
- Voice channel join/leave commands
- Playback controls: play, pause, resume, stop, skip, previous
- Queue management with auto-advance to next track
- Playlist CRUD: create, add, remove, rename
- Playlist persistence via JSON files
- Per-guild player instances for multi-server support
- Helper scripts for Windows (run.bat) and Linux/macOS (run.sh)
