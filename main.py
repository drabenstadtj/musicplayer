import curses
from player.navidrome import NavidromeClient
from ui.screens import MainMenuScreen, AlbumBrowserScreen, NowPlayingScreen, BluetoothSettingsScreen
from ui.theme import init_colors
from hardware.button_controller import ButtonController

class MusicPlayerApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        
        # Try to connect to Navidrome
        self.client = NavidromeClient()

        # Try to initialize audio player, fall back to mock if no audio device
        try:
            from player.audio import AudioPlayer
            self.audio = AudioPlayer()
        except Exception as e:
            from player.audio_mock import AudioPlayer
            self.audio = AudioPlayer()
        
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
        if not self.client.test_connection():
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, "Failed to connect to Navidrome server!")
            self.stdscr.addstr(1, 0, "Press any key to exit...")
            self.stdscr.refresh()
            self.stdscr.getch()
            return

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
                        # Try button emulator first, only call handle_input if not handled
                        handled_by_buttons = self._handle_keyboard_input(key)
                        if not handled_by_buttons:
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
                    elif result == "Settings":
                        self.show_settings()
                        break
                    elif result:
                        menu.draw()
        finally:
            self.cleanup()
    
    def _handle_keyboard_input(self, key):
        """Handle keyboard input via button emulator

        Returns:
            True if key was handled by button emulator, False otherwise
        """
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
                return True
        return False
    
    def show_albums(self):
        # Fetch all albums
        albums = self.client.get_all_albums()

        if not albums:
            return

        browser = AlbumBrowserScreen(self.stdscr, albums)
        self.current_screen = browser
        browser.draw()

        while self.running:
            key = self.stdscr.getch()

            result = None

            if key != -1:
                # Try button emulator first, only call handle_input if not handled
                handled_by_buttons = self._handle_keyboard_input(key)
                if not handled_by_buttons:
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
                    # Load from Navidrome
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
        now_playing = NowPlayingScreen(self.stdscr, self.audio, self.client)
        self.current_screen = now_playing
        now_playing.draw()

        while self.running:
            key = self.stdscr.getch()

            result = None

            if key != -1:
                # Try button emulator first, only call handle_input if not handled
                handled_by_buttons = self._handle_keyboard_input(key)
                if not handled_by_buttons:
                    result = now_playing.handle_input(key)

            # Check for button actions
            if hasattr(now_playing, '_pending_action') and now_playing._pending_action:
                result = now_playing._pending_action
                now_playing._pending_action = None

            if result == False or result == "back":
                break

            now_playing.draw()

    def show_settings(self):
        """Show settings menu"""
        bt_settings = BluetoothSettingsScreen(self.stdscr)
        self.current_screen = bt_settings
        bt_settings.draw()

        while self.running:
            key = self.stdscr.getch()

            result = None

            if key != -1:
                # Try button emulator first, only call handle_input if not handled
                handled_by_buttons = self._handle_keyboard_input(key)
                if not handled_by_buttons:
                    result = bt_settings.handle_input(key)

            # Check for button actions
            if hasattr(bt_settings, '_pending_action') and bt_settings._pending_action:
                result = bt_settings._pending_action
                bt_settings._pending_action = None

            if result == False or result == "back":
                break

            bt_settings.draw()

    def quit(self):
        self.running = False

    def cleanup(self):
        self.button_controller.stop()
        # Clean up current screen if it has cleanup method
        if self.current_screen and hasattr(self.current_screen, 'cleanup'):
            self.current_screen.cleanup()

def main(stdscr):
    app = MusicPlayerApp(stdscr)
    app.run()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting...")