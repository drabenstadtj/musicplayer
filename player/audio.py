import os
import subprocess
import time
from utils.logger import get_logger

logger = get_logger("audio")

# Set library path before importing vlc
# Common locations for libvlc on Raspberry Pi
possible_paths = [
    '/usr/lib/arm-linux-gnueabihf',
    '/usr/lib/aarch64-linux-gnu',
    '/usr/lib/x86_64-linux-gnu',
    '/usr/lib',
]

for path in possible_paths:
    if os.path.exists(path):
        current_ld_path = os.environ.get('LD_LIBRARY_PATH', '')
        if current_ld_path:
            os.environ['LD_LIBRARY_PATH'] = f"{path}:{current_ld_path}"
        else:
            os.environ['LD_LIBRARY_PATH'] = path
        break

# Try importing vlc and log any errors
try:
    import vlc
    vlc_import_success = True
    vlc_import_error = None
except Exception as e:
    vlc_import_success = False
    vlc_import_error = str(e)
    vlc = None

# Debug VLC loading
def _debug_vlc():
    """Debug VLC library loading"""
    logger.info("=== VLC Debug Info ===")
    logger.info(f"VLC import success: {vlc_import_success}")
    if not vlc_import_success:
        logger.error(f"VLC import error: {vlc_import_error}")
        return

    logger.info(f"LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'NOT SET')}")
    if vlc:
        logger.info(f"VLC module path: {vlc.__file__}")

    # Try to get VLC version
    try:
        if vlc:
            logger.info(f"VLC version: {vlc.libvlc_get_version()}")
    except Exception as e:
        logger.warning(f"Could not get VLC version: {e}")

    # Try to find libvlc.so
    try:
        import ctypes.util
        libvlc_path = ctypes.util.find_library('vlc')
        logger.info(f"libvlc.so location: {libvlc_path}")
    except Exception as e:
        logger.error(f"VLC debug error: {e}")

_debug_vlc()

class AudioPlayer:
    def __init__(self):
        logger.info("=== AudioPlayer Init ===")

        # Try to set Bluetooth as default sink before initializing VLC
        self._ensure_bluetooth_sink()

        try:
            # Create VLC instance with PulseAudio output and optimized buffering
            # Increase network caching to reduce choppy playback
            # Increase audio buffer for smoother output
            logger.info("Creating VLC instance...")

            # Create VLC instance with working args
            # Note: Some args like --audio-buffer, --clock-jitter, --audio-resampler
            # cause Instance() to return None on this VLC version, so we use minimal args
            self.instance = vlc.Instance(
                '--aout=pulse',              # Use PulseAudio for audio output
                '--verbose=0',               # Minimal logging
                '--network-caching=30000',   # 30 second buffer for streaming (reduce choppiness)
                '--file-caching=10000',      # 10 second file cache
                '--live-caching=10000'       # 10 second live stream cache
            )
            logger.info(f"VLC instance created: {self.instance}")

            if self.instance is None:
                raise Exception("VLC Instance() returned None - VLC libraries not properly installed")

            logger.info("Creating media player...")
            self.player = self.instance.media_player_new()

            if self.player is None:
                raise Exception("media_player_new() returned None")

            self.audio_available = True
            logger.info("✓ Audio initialized with VLC + PulseAudio backend")
        except Exception as e:
            logger.error(f"Could not initialize audio device: {e}")
            logger.warning("Running in silent mode - no audio output available")
            self.audio_available = False
            raise  # Re-raise to trigger fallback to mock player

        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 100  # VLC uses 0-200 scale (100 = normal, 200 = amplified)

        if self.audio_available:
            self.player.audio_set_volume(self.volume)
            logger.info(f"Initial volume set to {self.volume}")

    def _ensure_bluetooth_sink(self):
        """Ensure Bluetooth sink is set as default if available"""
        try:
            # Get list of sinks
            result = subprocess.run(
                ['pactl', 'list', 'short', 'sinks'],
                capture_output=True,
                text=True,
                timeout=2
            )

            logger.debug("Available PulseAudio sinks:")
            logger.debug(result.stdout)

            # Look for bluez sink
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and 'bluez' in parts[1].lower():
                    bluez_sink = parts[1]
                    logger.info(f"Found Bluetooth sink: {bluez_sink}")
                    # Set as default
                    subprocess.run(['pactl', 'set-default-sink', bluez_sink], timeout=2)
                    logger.info(f"Set {bluez_sink} as default audio sink")

                    # Set the PULSE_SINK environment variable for this process
                    os.environ['PULSE_SINK'] = bluez_sink
                    logger.info(f"Set PULSE_SINK environment variable to {bluez_sink}")
                    return

            logger.info("No Bluetooth sink found - using default audio sink")
        except Exception as e:
            logger.warning(f"Could not set Bluetooth sink: {e}")

    def play(self, stream_url, song_info):
        """Stream a song from URL"""
        # Set current_song immediately so UI shows info even if playback fails
        self.current_song = song_info

        try:
            logger.info(f"=== Attempting to stream ===")
            logger.info(f"Song: {song_info.get('title', 'Unknown')}")
            logger.info(f"Artist: {song_info.get('artist', 'Unknown')}")
            logger.debug(f"URL: {stream_url}")

            if not self.audio_available:
                logger.warning("⚠ Audio not available - simulating playback")
                self.is_playing = True
                self.is_paused = False
                return True

            # Stop current playback
            self.stop()

            logger.debug("Creating media from URL...")
            media = self.instance.media_new(stream_url)
            self.player.set_media(media)

            logger.info("Starting stream playback...")
            self.player.play()

            self.is_playing = True
            self.is_paused = False

            # Wait for VLC to start playing and check state
            for i in range(10):  # Check for up to 5 seconds
                time.sleep(0.5)
                state = self.player.get_state()
                logger.debug(f"VLC state after {(i+1)*0.5}s: {state}")

                # VLC states: 0=NothingSpecial, 1=Opening, 2=Buffering, 3=Playing, 4=Paused, 5=Stopped, 6=Ended, 7=Error
                if state == 3:  # Playing
                    logger.info("✓ VLC is now playing!")
                    break
                elif state == 7:  # Error
                    logger.error("✗ VLC encountered an error!")
                    break

            # Check if audio stream was created in PulseAudio
            result = subprocess.run(['pactl', 'list', 'short', 'sink-inputs'],
                                  capture_output=True, text=True, timeout=2)
            if result.stdout.strip():
                logger.debug(f"✓ Audio stream active: {result.stdout.strip()}")
            else:
                logger.warning("No PulseAudio sink-input detected!")
                logger.warning("This could mean VLC is not outputting to PulseAudio.")

                # Check what audio output VLC is using
                logger.debug(f"VLC audio output module: {self.player.audio_output_device_enum()}")

            return True

        except Exception as e:
            logger.error(f"✗ Error streaming song: {e}", exc_info=True)
            # Keep current_song set so UI can display info
            self.is_playing = False
            return False

    def pause(self):
        """Pause playback"""
        if not self.audio_available:
            self.is_paused = True
            return

        if self.is_playing and not self.is_paused:
            logger.info("Pausing playback")
            self.player.pause()
            self.is_paused = True

    def unpause(self):
        """Resume playback"""
        if not self.audio_available:
            self.is_paused = False
            return

        if self.is_playing and self.is_paused:
            logger.info("Resuming playback")
            self.player.pause()  # VLC's pause() toggles, so call again to unpause
            self.is_paused = False

    def toggle_pause(self):
        """Toggle pause/play"""
        if self.is_paused:
            self.unpause()
        else:
            self.pause()

    def stop(self):
        """Stop playback"""
        if self.audio_available:
            logger.info("Stopping playback")
            self.player.stop()

        self.is_playing = False
        self.is_paused = False

    def set_volume(self, volume):
        """Set volume (0.0 to 2.0)"""
        # Convert 0.0-2.0 to 0-200 for VLC (allows amplification above 100%)
        self.volume = max(0, min(200, int(volume * 100)))
        logger.debug(f"Setting volume to {self.volume}")
        if self.audio_available:
            self.player.audio_set_volume(self.volume)

    def volume_up(self, step=10):
        """Increase volume"""
        old_volume = self.volume
        self.volume = max(0, min(200, self.volume + step))
        logger.debug(f"Volume up: {old_volume} -> {self.volume}")
        if self.audio_available:
            self.player.audio_set_volume(self.volume)

    def volume_down(self, step=10):
        """Decrease volume"""
        old_volume = self.volume
        self.volume = max(0, min(200, self.volume - step))
        logger.debug(f"Volume down: {old_volume} -> {self.volume}")
        if self.audio_available:
            self.player.audio_set_volume(self.volume)

    def get_position(self):
        """Get current playback position in seconds"""
        if not self.audio_available:
            return 0
        if self.is_playing:
            # VLC returns position in milliseconds
            pos = self.player.get_time()
            return pos / 1000.0 if pos >= 0 else 0
        return 0

    def is_finished(self):
        """Check if current song has finished"""
        if not self.audio_available:
            return False
        if self.is_playing:
            state = self.player.get_state()
            # VLC states: 0=NothingSpecial, 1=Opening, 2=Buffering, 3=Playing, 4=Paused, 5=Stopped, 6=Ended, 7=Error
            return state == 6  # vlc.State.Ended
        return False
