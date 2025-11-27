import pygame
import requests
import tempfile
import os
from io import BytesIO

class AudioPlayer:
    def __init__(self):
        # Force pygame to use ALSA and the default device
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        os.environ['AUDIODEV'] = 'default'
        
        # Initialize pygame mixer quietly
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.temp_file = None
        pygame.mixer.music.set_volume(self.volume)
        
    def play(self, stream_url, song_info):
        """Play a song from URL"""
        try:
            # Stop current playback
            self.stop()
            
            # Download audio with larger chunks for speed
            response = requests.get(stream_url, timeout=5)
            response.raise_for_status()
            
            # Save to temporary file
            if self.temp_file and os.path.exists(self.temp_file):
                os.remove(self.temp_file)
            
            # Create temp file
            suffix = '.mp3'
            fd, self.temp_file = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            
            # Write all at once (faster than chunked)
            with open(self.temp_file, 'wb') as f:
                f.write(response.content)
            
            # Load and play
            pygame.mixer.music.load(self.temp_file)
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
        pygame.mixer.music.set_volume(self.volume)
    
    def volume_up(self, step=0.1):
        """Increase volume"""
        self.set_volume(self.volume + step)
    
    def volume_down(self, step=0.1):
        """Decrease volume"""
        self.set_volume(self.volume - step)
    
    def get_volume(self):
        """Get current volume"""
        return self.volume
    
    def get_position(self):
        """Get current playback position in seconds"""
        if self.is_playing:
            return pygame.mixer.music.get_pos() / 1000.0
        return 0
    
    def is_finished(self):
        """Check if current song has finished"""
        return self.is_playing and not pygame.mixer.music.get_busy()