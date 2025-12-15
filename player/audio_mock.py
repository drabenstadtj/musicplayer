class AudioPlayer:
    """Mock audio player for testing without sound"""
    def __init__(self):
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        
    def play(self, stream_url, song_info):
        print(f"Mock: Playing {song_info.get('title', 'Unknown')}")
        self.current_song = song_info
        self.is_playing = True
        self.is_paused = False
        return True
    
    def pause(self):
        if self.is_playing and not self.is_paused:
            print("Mock: Paused")
            self.is_paused = True
    
    def unpause(self):
        if self.is_playing and self.is_paused:
            print("Mock: Unpaused")
            self.is_paused = False
    
    def toggle_pause(self):
        if self.is_paused:
            self.unpause()
        else:
            self.pause()
    
    def stop(self):
        print("Mock: Stopped")
        self.is_playing = False
        self.is_paused = False
    
    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        print(f"Mock: Volume set to {int(self.volume * 100)}%")
    
    def volume_up(self, step=0.1):
        self.set_volume(self.volume + step)
    
    def volume_down(self, step=0.1):
        self.set_volume(self.volume - step)
    
    def get_position(self):
        return 0
    
    def is_finished(self):
        return False