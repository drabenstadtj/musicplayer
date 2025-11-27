"""
Local Audio Player - plays files directly from filesystem
"""

import pygame
import os

class LocalAudioPlayer:
    def __init__(self):
        # Force pygame to use ALSA
        os.environ['SDL_AUDIODRIVER'] = 'alsa'
        os.environ['AUDIODEV'] = 'default'
        
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
        
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        pygame.mixer.music.set_volume(self.volume)
    
    def play(self, filepath, song_info=None):
        """Play a local file"""
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            
            self.current_song = song_info or {'title': os.path.basename(filepath)}
            self.is_playing = True
            self.is_paused = False
            
            return True
        except Exception as e:
            print(f"Error playing file: {e}")
            return False
    
    def pause(self):
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
    
    def unpause(self):
        if self.is_playing and self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
    
    def toggle_pause(self):
        if self.is_paused:
            self.unpause()
        else:
            self.pause()
    
    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
    
    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
    
    def volume_up(self, step=0.1):
        self.set_volume(self.volume + step)
    
    def volume_down(self, step=0.1):
        self.set_volume(self.volume - step)
    
    def get_volume(self):
        return self.volume