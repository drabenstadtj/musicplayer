import curses
from player.navidrome import NavidromeClient
try:
    from player.audio import AudioPlayer
except:
    from player.audio_mock import AudioPlayer
    print("Using mock audio player (no sound)")
from ui.screens import MainMenuScreen, AlbumBrowserScreen, NowPlayingScreen
from ui.theme import init_colors

class MusicPlayerApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.client = NavidromeClient()
        self.audio = AudioPlayer()
        
        # Setup curses
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(1)  # Non-blocking input
        self.stdscr.timeout(100)  # Refresh every 100ms
        init_colors()
        
        self.current_screen = None
    
    def run(self):
        # Test connection
        if not self.client.test_connection():
            self.stdscr.addstr(0, 0, "Failed to connect to Navidrome server!")
            self.stdscr.addstr(1, 0, "Press any key to exit...")
            self.stdscr.refresh()
            self.stdscr.getch()
            return
        
        # Start with main menu
        running = True
        while running:
            menu = MainMenuScreen(self.stdscr)
            menu.draw()
            
            while True:
                key = self.stdscr.getch()
                if key == -1:  # No input
                    continue
                    
                result = menu.handle_input(key)
                
                if result == False:
                    running = False
                    break
                elif result == "Albums":
                    self.show_albums()
                    break
                elif result == "Playlists":
                    # TODO: implement playlists
                    break
                elif result == True:
                    menu.draw()
    
    def show_albums(self):
        # Fetch albums
        albums = self.client.get_albums(limit=100)
        
        if not albums:
            return
        
        browser = AlbumBrowserScreen(self.stdscr, albums)
        browser.draw()
        
        while True:
            key = self.stdscr.getch()
            if key == -1:
                continue
                
            result = browser.handle_input(key)
            
            if result == False or result == "back":
                break
            elif isinstance(result, tuple):
                action, data = result
                if action == "load_album":
                    songs = self.client.get_album_songs(data)
                    browser.set_songs(songs)
                elif action == "play_song":
                    self.play_song(data)
                    self.show_now_playing()
                    break
            
            browser.draw()
    
    def play_song(self, song):
        """Start playing a song"""
        stream_url = self.client.get_stream_url(song['id'])
        if stream_url:
            self.audio.play(stream_url, song)
    
    def show_now_playing(self):
        """Show now playing screen"""
        now_playing = NowPlayingScreen(self.stdscr, self.audio)
        now_playing.draw()
        
        while True:
            key = self.stdscr.getch()
            if key != -1:
                result = now_playing.handle_input(key)
                if result == False or result == "back":
                    break
            
            now_playing.draw()

def main(stdscr):
    app = MusicPlayerApp(stdscr)
    app.run()

if __name__ == "__main__":
    curses.wrapper(main)