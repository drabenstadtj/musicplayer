import pygame
import requests
import threading
import time
from io import BytesIO

class AudioPlayer:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            self.audio_available = True
        except pygame.error as e:
            print(f"Warning: Could not initialize audio device: {e}")
            print("Running in silent mode - no audio output available")
            self.audio_available = False
            raise  # Re-raise to trigger fallback to mock player

        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7

        if self.audio_available:
            pygame.mixer.music.set_volume(self.volume)
        
    def play(self, stream_url, song_info):
        """Play a song from URL"""
        try:
            # Stop current playback
            self.stop()
            
            # Download and play
            response = requests.get(stream_url, stream=True, timeout=10)
            response.raise_for_status()
            
            # Load into pygame
            audio_data = BytesIO(response.content)
            pygame.mixer.music.load(audio_data)
            pygame.mixer.music.play()
            
            self.current_song = song_info
            self.is_playing = True
            self.is_paused = False
            
            return True
            
        except Exception as e:
            print(f"Error playing song: {e}")
            return False
    
    def pause(self):
        """Pause playback"""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
    
    def unpause(self):
        """Resume playback"""
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
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
    
    def set_volume(self, volume):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
    
    def volume_up(self, step=0.1):
        """Increase volume"""
        self.set_volume(self.volume + step)
    
    def volume_down(self, step=0.1):
        """Decrease volume"""
        self.set_volume(self.volume - step)
    
    def get_position(self):
        """Get current playback position in seconds"""
        if self.is_playing:
            return pygame.mixer.music.get_pos() / 1000.0
        return 0
    
    def is_finished(self):
        """Check if current song has finished"""
        return self.is_playing and not pygame.mixer.music.get_busy()