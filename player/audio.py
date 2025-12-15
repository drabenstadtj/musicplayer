import pygame
import requests
import tempfile
import os
from io import BytesIO

class AudioPlayer:
    def __init__(self):
        # Configure SDL to use PulseAudio instead of ALSA
        os.environ['SDL_AUDIODRIVER'] = 'pulseaudio'

        try:
            # Initialize pygame with PulseAudio backend
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            self.audio_available = True
            print("✓ Audio initialized with PulseAudio backend")
        except pygame.error as e:
            print(f"Warning: Could not initialize audio device: {e}")
            print("Running in silent mode - no audio output available")
            self.audio_available = False
            raise  # Re-raise to trigger fallback to mock player

        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.temp_file = None

        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
        
    def play(self, stream_url, song_info):
        """Play a song from URL"""
        # Set current_song immediately so UI shows info even if playback fails
        self.current_song = song_info

        try:
            print(f"\n=== Attempting to play ===")
            print(f"Song: {song_info.get('title', 'Unknown')}")

            if not self.audio_available:
                print("⚠ Audio not available - simulating playback")
                self.is_playing = True
                self.is_paused = False
                return True

            # Stop current playback
            self.stop()

            print("Downloading audio...")
            response = requests.get(stream_url, stream=True, timeout=10)
            response.raise_for_status()

            print(f"Download complete. Size: {len(response.content)} bytes")

            # Save to temporary file
            if self.temp_file and os.path.exists(self.temp_file):
                os.remove(self.temp_file)

            # Create temp file with appropriate extension
            suffix = '.mp3'  # We're requesting mp3 format
            fd, self.temp_file = tempfile.mkstemp(suffix=suffix)
            os.close(fd)

            with open(self.temp_file, 'wb') as f:
                f.write(response.content)

            print(f"Saved to: {self.temp_file}")
            print("Loading into pygame...")
            pygame.mixer.music.load(self.temp_file)

            print("Starting playback...")
            pygame.mixer.music.play()

            self.is_playing = True
            self.is_paused = False

            print("✓ Playback started successfully!")
            return True

        except Exception as e:
            print(f"✗ Error playing song: {e}")
            import traceback
            traceback.print_exc()
            # Keep current_song set so UI can display info
            self.is_playing = False
            return False
    
    def pause(self):
        """Pause playback"""
        if not self.audio_available:
            self.is_paused = True
            print("⚠ Simulated pause")
            return
            
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True

    def unpause(self):
        """Resume playback"""
        if not self.audio_available:
            self.is_paused = False
            print("⚠ Simulated unpause")
            return
            
        if self.is_playing and self.is_paused:
            pygame.mixer.music.unpause()
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
            pygame.mixer.music.stop()
        else:
            print("⚠ Simulated stop")
            
        self.is_playing = False
        self.is_paused = False
        
        # Clean up temp file
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
            self.temp_file = None

    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
        else:
            print(f"⚠ Simulated volume: {int(self.volume * 100)}%")

    def volume_up(self, step=0.1):
        """Increase volume"""
        self.set_volume(self.volume + step)

    def volume_down(self, step=0.1):
        """Decrease volume"""
        self.set_volume(self.volume - step)

    def get_position(self):
        """Get current playback position in seconds"""
        if not self.audio_available:
            return 0
        if self.is_playing:
            return pygame.mixer.music.get_pos() / 1000.0
        return 0

    def is_finished(self):
        """Check if current song has finished"""
        if not self.audio_available:
            return False
        return self.is_playing and not pygame.mixer.music.get_busy()