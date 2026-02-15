# Changelog

## v1.3.0 - 2026-02-14

### Added
- `/silent` command to toggle silent mode — suppresses auto chat messages, makes command responses ephemeral
- `/clearcache` command to clear the downloaded audio file cache
- Clickable song titles in all bot messages (markdown links to YouTube)
- Cross-platform opus loading (Windows + Linux support)

### Changed
- Switched audio format from MP3 (192kbps) to Opus (128kbps) for better quality at lower bitrate
- Eliminated duplicate "Now playing" announcements when using `/play`, `/skip`, `/previous`, `/restart`
- Removed old project plan file

## v1.2.0 - 2026-02-14

### Added
- Smart prefetching: next chillax track downloads while current song plays for gapless playback
- "Up next" announcements in chat when a track is prefetched
- `/reroll` command to discard the prefetched pick and get a new suggestion
- Downloaded MP3s now named as `Artist - Album - Title.mp3` (falls back to `Artist - Title.mp3`)

### Fixed
- Cascading prefetch bug when restarting chillax mid-song (generation counter approach)

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
