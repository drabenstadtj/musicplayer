import vlc
import os
import subprocess
import time

class AudioPlayer:
    def __init__(self):
        # Open log file for debugging
        self.logfile = open('/tmp/musicplayer_audio.log', 'a')
        self._log("=== AudioPlayer Init ===")

        # Try to set Bluetooth as default sink before initializing VLC
        self._ensure_bluetooth_sink()

        try:
            # Create VLC instance with PulseAudio output and optimized buffering
            # Increase network caching to reduce choppy playback
            # Increase audio buffer for smoother output
            self._log("Creating VLC instance...")
            self.instance = vlc.Instance(
                '--aout=pulse',
                '--verbose=0',
                '--network-caching=3000',     # 3 second network cache
                '--audio-buffer=500',          # 500ms audio buffer
                '--clock-jitter=1000',         # Allow 1s clock jitter
                '--audio-resampler=soxr',      # High quality resampler
            )

            self._log(f"VLC instance created: {self.instance}")

            if self.instance is None:
                raise Exception("VLC Instance() returned None - VLC libraries not properly installed")

            self._log("Creating media player...")
            self.player = self.instance.media_player_new()

            if self.player is None:
                raise Exception("media_player_new() returned None")

            self.audio_available = True
            self._log("✓ Audio initialized with VLC + PulseAudio backend")
        except Exception as e:
            self._log(f"Warning: Could not initialize audio device: {e}")
            self._log("Running in silent mode - no audio output available")
            self.audio_available = False
            raise  # Re-raise to trigger fallback to mock player

        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 70  # VLC uses 0-100 scale

        if self.audio_available:
            self.player.audio_set_volume(self.volume)

    def _log(self, message):
        """Write to log file"""
        self.logfile.write(f"{message}\n")
        self.logfile.flush()

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

            self._log("Available sinks:")
            self._log(result.stdout)

            # Look for bluez sink
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and 'bluez' in parts[1].lower():
                    bluez_sink = parts[1]
                    self._log(f"Found Bluetooth sink: {bluez_sink}")
                    # Set as default
                    subprocess.run(['pactl', 'set-default-sink', bluez_sink], timeout=2)
                    self._log(f"Set {bluez_sink} as default audio sink")

                    # Set the PULSE_SINK environment variable for this process
                    os.environ['PULSE_SINK'] = bluez_sink
                    self._log(f"Set PULSE_SINK environment variable to {bluez_sink}")
                    return

            self._log("No Bluetooth sink found - using default")
        except Exception as e:
            self._log(f"Could not set Bluetooth sink: {e}")

    def play(self, stream_url, song_info):
        """Stream a song from URL"""
        # Set current_song immediately so UI shows info even if playback fails
        self.current_song = song_info

        try:
            self._log(f"\n=== Attempting to stream ===")
            self._log(f"Song: {song_info.get('title', 'Unknown')}")
            self._log(f"URL: {stream_url}")

            if not self.audio_available:
                self._log("⚠ Audio not available - simulating playback")
                self.is_playing = True
                self.is_paused = False
                return True

            # Stop current playback
            self.stop()

            self._log("Creating media from URL...")
            media = self.instance.media_new(stream_url)
            self.player.set_media(media)

            self._log("Starting stream playback...")
            self.player.play()

            self.is_playing = True
            self.is_paused = False

            self._log("✓ Stream started successfully!")

            # Check if audio stream was created
            time.sleep(0.5)  # Give PulseAudio time to create the stream
            result = subprocess.run(['pactl', 'list', 'short', 'sink-inputs'],
                                  capture_output=True, text=True, timeout=2)
            if result.stdout.strip():
                self._log(f"Audio stream active: {result.stdout.strip()}")
            else:
                self._log("WARNING: No audio stream detected! VLC might not be outputting audio.")
                self._log("Try: pactl list sink-inputs")

            return True

        except Exception as e:
            self._log(f"✗ Error streaming song: {e}")
            import traceback
            self._log(traceback.format_exc())
            # Keep current_song set so UI can display info
            self.is_playing = False
            return False

    def pause(self):
        """Pause playback"""
        if not self.audio_available:
            self.is_paused = True
            return

        if self.is_playing and not self.is_paused:
            self.player.pause()
            self.is_paused = True

    def unpause(self):
        """Resume playback"""
        if not self.audio_available:
            self.is_paused = False
            return

        if self.is_playing and self.is_paused:
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
            self.player.stop()

        self.is_playing = False
        self.is_paused = False

    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)"""
        # Convert 0.0-1.0 to 0-100 for VLC
        self.volume = max(0, min(100, int(volume * 100)))
        if self.audio_available:
            self.player.audio_set_volume(self.volume)

    def volume_up(self, step=0.1):
        """Increase volume"""
        current = self.volume / 100.0
        self.set_volume(current + step)

    def volume_down(self, step=0.1):
        """Decrease volume"""
        current = self.volume / 100.0
        self.set_volume(current - step)

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
