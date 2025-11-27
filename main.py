import curses
from player.navidrome import NavidromeClient
from player.local_library import LocalLibrary
try:
    from player.audio import AudioPlayer
    from player.audio_local import LocalAudioPlayer
except:
    from player.audio_mock import AudioPlayer
    LocalAudioPlayer = AudioPlayer
    print("Using mock audio player (no sound)")
from ui.screens import MainMenuScreen, AlbumBrowserScreen, NowPlayingScreen
from ui.theme import init_colors
from hardware.button_controller import ButtonController

class MusicPlayerApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        
        # Try to connect to Navidrome
        self.client = NavidromeClient()
        self.navidrome_available = False
        
        # Setup local library
        self.local_library = LocalLibrary()
        
        # Audio player (will switch based on source)
        self.audio = None
        self.local_audio = None
        
        # Setup curses
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)
        init_colors()
        
        self.current_screen = None
        self.running = True
        
        # Initialize button controller
        self.button_controller = ButtonController(self, use_gpio=True)
        self.button_controller.start()
    
    def run(self):
        # Test Navidrome connection
        self.navidrome_available = self.client.test_connection()
        
        if self.navidrome_available:
            self.audio = AudioPlayer()
            status = "Connected to Navidrome"
        else:
            status = "Offline - Local library only"
        
        # Scan local library
        self.local_library.scan()
        self.local_audio = LocalAudioPlayer()
        
        # Show status briefly
        self.stdscr.clear()
        self.stdscr.addstr(0, 0, status)
        self.stdscr.addstr(1, 0, f"Local songs: {len(self.local_library.songs)}")
        self.stdscr.addstr(2, 0, "Press any key to continue...")
        self.stdscr.refresh()
        self.stdscr.timeout(-1)  # Wait for key
        self.stdscr.getch()
        self.stdscr.timeout(100)  # Back to non-blocking
        
        # Start with main menu
        try:
            while self.running:
                menu = MainMenuScreen(self.stdscr)
                self.current_screen = menu
                menu.draw()
                
                while self.running:
                    key = self.stdscr.getch()
                    
                    result = None
                    
                    if key != -1:
                        self._handle_keyboard_input(key)
                        result = menu.handle_input(key)
                    
                    # Check for button actions
                    if hasattr(menu, '_pending_action') and menu._pending_action:
                        result = menu._pending_action
                        menu._pending_action = None
                    
                    if result == False:
                        self.running = False
                        break
                    elif result == "Albums":
                        self.show_albums()
                        break
                    elif result == "Playlists":
                        # TODO: implement playlists
                        break
                    elif result:
                        menu.draw()
        finally:
            self.cleanup()
    
    def _handle_keyboard_input(self, key):
        from hardware.buttons import KeyboardButtonEmulator
        
        if isinstance(self.button_controller.handler, KeyboardButtonEmulator):
            key_map = {
                curses.KEY_UP: 'KEY_UP',
                curses.KEY_DOWN: 'KEY_DOWN',
                curses.KEY_BACKSPACE: 'KEY_BACKSPACE',
                127: 'KEY_BACKSPACE',
                10: '\n',
            }
            
            mapped_key = key_map.get(key)
            if mapped_key:
                self.button_controller.handler.handle_key(mapped_key)
    
    def show_albums(self):
        """Show albums from both Navidrome and local library"""
        albums = []
        
        # Get local albums
        local_albums = self.local_library.get_albums()
        for album in local_albums:
            album['source'] = 'local'
            album['name'] = f"📁 {album['name']}"  # Add icon for local
        albums.extend(local_albums)
        
        # Get Navidrome albums if available
        if self.navidrome_available:
            navidrome_albums = self.client.get_albums(limit=100)
            for album in navidrome_albums:
                album['source'] = 'navidrome'
                album['name'] = f"☁️ {album['name']}"  # Add icon for cloud
            albums.extend(navidrome_albums)
        
        if not albums:
            return
        
        # Sort combined list
        albums.sort(key=lambda a: a['name'])
        
        browser = AlbumBrowserScreen(self.stdscr, albums)
        self.current_screen = browser
        browser.draw()
        
        while self.running:
            key = self.stdscr.getch()
            
            result = None
            
            if key != -1:
                self._handle_keyboard_input(key)
                result = browser.handle_input(key)
            
            # Check for button actions
            if hasattr(browser, '_pending_action') and browser._pending_action:
                result = browser._pending_action
                browser._pending_action = None
            
            if result == False or result == "back":
                break
            elif isinstance(result, tuple):
                action, data = result
                if action == "load_album":
                    # Get the album source
                    album = browser.albums[browser.album_index]
                    
                    if album['source'] == 'local':
                        # Load from local library
                        songs = self.local_library.get_album_songs(album['id'])
                    else:
                        # Load from Navidrome
                        songs = self.client.get_album_songs(data)
                    
                    # Mark songs with their source
                    for song in songs:
                        song['source'] = album['source']
                    
                    browser.set_songs(songs)
                    
                elif action == "play_song":
                    self.play_song(data)
                    self.show_now_playing()
                    break
            
            browser.draw()
    
    def play_song(self, song):
        """Play a song from either local or Navidrome"""
        if song.get('source') == 'local':
            # Play local file
            self.local_audio.play(song['path'], song)
            self.current_player = self.local_audio
        else:
            # Play from Navidrome
            stream_url = self.client.get_stream_url(song['id'])
            if stream_url:
                self.audio.play(stream_url, song)
                self.current_player = self.audio
    
    def show_now_playing(self):
        """Show now playing screen"""
        now_playing = NowPlayingScreen(self.stdscr, self.current_player)
        self.current_screen = now_playing
        now_playing.draw()
        
        while self.running:
            key = self.stdscr.getch()
            
            result = None
            
            if key != -1:
                self._handle_keyboard_input(key)
                result = now_playing.handle_input(key)
            
            # Check for button actions
            if hasattr(now_playing, '_pending_action') and now_playing._pending_action:
                result = now_playing._pending_action
                now_playing._pending_action = None
            
            if result == False or result == "back":
                break
            
            now_playing.draw()
    
    def quit(self):
        self.running = False
    
    def cleanup(self):
        self.button_controller.stop()

def main(stdscr):
    app = MusicPlayerApp(stdscr)
    app.run()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting...")