# Music Player Logging System

This directory contains the centralized logging system for the Music Player application.

## Log Files

All logs are stored in `/tmp/musicplayer_logs/`:

- **musicplayer.log** - Main application logs (navigation, user actions)
- **audio.log** - Audio playback logs (VLC, PulseAudio, streaming details) [DEBUG level]
- **ui.log** - UI rendering and screen updates
- **hardware.log** - Button events and GPIO interactions
- **network.log** - Network requests to Navidrome server [DEBUG level]

## Log Rotation

Logs automatically rotate when they reach 5MB, keeping 3 backup files:
- `musicplayer.log` (current)
- `musicplayer.log.1` (previous)
- `musicplayer.log.2` (older)
- `musicplayer.log.3` (oldest)

## Usage

```python
from utils.logger import get_logger

logger = get_logger("main")  # or "audio", "ui", "hardware", "network"

logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
logger.exception("Error with full stack trace")
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (VLC states, UI updates)
- **INFO**: General informational messages (navigation, playback events)
- **WARNING**: Warning messages (missing features, fallback behavior)
- **ERROR**: Error messages with stack traces

## Viewing Logs

On the Raspberry Pi:
```bash
# View real-time logs
tail -f /tmp/musicplayer_logs/musicplayer.log
tail -f /tmp/musicplayer_logs/audio.log

# View all logs
cat /tmp/musicplayer_logs/musicplayer.log

# Search logs
grep "ERROR" /tmp/musicplayer_logs/*.log
```

## Log Format

```
YYYY-MM-DD HH:MM:SS | logger_name | LEVEL | message
```

Example:
```
2025-01-15 14:23:45 | audio | INFO | ✓ VLC is now playing!
2025-01-15 14:23:46 | main | INFO | Navigating to Albums
```
