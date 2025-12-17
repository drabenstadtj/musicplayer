
import curses
from player.navidrome import NavidromeClient
from ui.screens import (MainMenuScreen, AlbumBrowserScreen, SongListScreen, NowPlayingScreen,
                        BluetoothSettingsScreen, ArtistBrowserScreen, PlaylistBrowserScreen)
from ui.theme import init_colors
from hardware.button_controller import ButtonController
from utils.logger import get_logger, log_startup, log_shutdown

logger = get_logger("main")

class MusicPlayerApp:
    def __init__(self, stdscr):
        logger.info("Initializing MusicPlayerApp")
        self.stdscr = stdscr

        # Try to connect to Navidrome
        logger.info("Connecting to Navidrome client")
        self.client = NavidromeClient()

        # Try to initialize audio player, fall back to mock if no audio device
        try:
            logger.info("Initializing audio player")
            from player.audio import AudioPlayer
            self.audio = AudioPlayer()
        except Exception as e:
            logger.warning(f"Failed to initialize audio player, using mock: {e}")
            from player.audio_mock import AudioPlayer
            self.audio = AudioPlayer()

        # Setup curses
        logger.debug("Setting up curses interface")
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)
        init_colors()

        self.current_screen = None
        self.running = True

        # Cache for metadata
        self.cached_albums = None
        self.cached_artists = None
        self.cached_playlists = None

        # Track if now playing screen is available
        self.has_active_playback = False
        self.should_return_to_now_playing = False

        # Initialize button controller
        logger.info("Initializing button controller")
        self.button_controller = ButtonController(self, use_gpio=True)
        self.button_controller.start()
        logger.info("MusicPlayerApp initialization complete")
    
    def run(self):
        logger.info("Starting main application loop")
        # Test Navidrome connection
        if not self.client.test_connection():
            logger.error("Failed to connect to Navidrome server")
            self.stdscr.clear()
            self.stdscr.addstr(0, 0, "Failed to connect to Navidrome server!")
            self.stdscr.addstr(1, 0, "Press any key to exit...")
            self.stdscr.refresh()
            self.stdscr.getch()
            return

        logger.info("Navidrome connection successful")
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
                        logger.info("User quit from main menu")
                        self.running = False
                        break
                    elif result == "Albums":
                        logger.info("Navigating to Albums")
                        self.show_albums()
                        break
                    elif result == "Artists":
                        logger.info("Navigating to Artists")
                        self.show_artists()
                        break
                    elif result == "Playlists":
                        logger.info("Navigating to Playlists")
                        self.show_playlists()
                        break
                    elif result == "Settings":
                        logger.info("Navigating to Settings")
                        self.show_settings()
                        break
                    elif result:
                        menu.draw()
        finally:
            logger.info("Application shutting down")
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
        # Use cached albums if available, otherwise fetch from Navidrome
        if self.cached_albums is None:
            logger.info("Fetching albums from Navidrome")
            albums = self.client.get_all_albums()
            self.cached_albums = albums
            logger.info(f"Cached {len(albums)} albums")
        else:
            logger.debug("Using cached albums")
            albums = self.cached_albums

        if not albums:
            logger.warning("No albums found")
            return

        browser = AlbumBrowserScreen(self.stdscr, albums)
        self.current_screen = browser
        browser.draw()

        while self.running:
            # Check for now playing combo
            if self.should_return_to_now_playing:
                self.should_return_to_now_playing = False
                self.show_now_playing()
                # Restore current_screen to browser after returning
                self.current_screen = browser
                browser.draw()
                continue

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
                logger.info("Returning to main menu from albums")
                break
            elif isinstance(result, tuple):
                action, data = result
                if action == "select_album":
                    logger.info(f"Album selected: {data.get('name', 'Unknown')}")
                    # Show song list screen (this will return when user presses back)
                    self.show_song_list(data)
                    # Restore current_screen to browser after returning from song list
                    self.current_screen = browser
                    browser.draw()

            browser.draw()

    def show_song_list(self, album):
        """Show song list for an album"""
        logger.info(f"Loading songs for album: {album.get('name', 'Unknown')}")
        # Load songs from Navidrome
        songs = self.client.get_album_songs(album['id'])

        if not songs:
            logger.warning(f"No songs found for album: {album.get('name', 'Unknown')}")
            return

        logger.info(f"Loaded {len(songs)} songs")

        song_list = SongListScreen(self.stdscr, album, songs)
        self.current_screen = song_list
        song_list.draw()

        while self.running:
            # Check for now playing combo
            if self.should_return_to_now_playing:
                self.should_return_to_now_playing = False
                self.show_now_playing()
                # Restore current_screen to song_list after returning
                self.current_screen = song_list
                song_list.draw()
                continue

            key = self.stdscr.getch()

            result = None

            if key != -1:
                # Try button emulator first, only call handle_input if not handled
                handled_by_buttons = self._handle_keyboard_input(key)
                if not handled_by_buttons:
                    result = song_list.handle_input(key)

            # Check for button actions
            if hasattr(song_list, '_pending_action') and song_list._pending_action:
                result = song_list._pending_action
                song_list._pending_action = None

            if result == False:
                logger.info("Exiting song list (returning to album browser)")
                return  # Return to album browser
            elif result == "back":
                logger.info("Back pressed in song list")
                return  # Return to album browser
            elif isinstance(result, tuple):
                action, data = result
                if action == "play_song":
                    logger.info(f"Playing song: {data.get('title', 'Unknown')}")
                    self.play_song(data)
                    self.show_now_playing()
                    # Restore current_screen to song_list after returning
                    self.current_screen = song_list
                    song_list.draw()

            song_list.draw()

    def play_song(self, song):
        """Start playing a song"""
        logger.info(f"Requesting stream for song: {song.get('title', 'Unknown')} by {song.get('artist', 'Unknown')}")
        stream_url = self.client.get_stream_url(song['id'])
        if stream_url:
            logger.info(f"Stream URL obtained: {stream_url}")
            self.audio.play(stream_url, song)
            self.has_active_playback = True
        else:
            logger.error(f"Failed to get stream URL for song: {song.get('title', 'Unknown')}")

    def show_now_playing(self):
        """Show now playing screen"""
        logger.info("Showing now playing screen")
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

            if result == False:
                logger.info("Exiting now playing screen")
                return  # Exit and return to previous screen
            elif result == "back":
                logger.info("Back pressed in now playing screen")
                return  # Exit and return to previous screen

            now_playing.draw()

    def show_settings(self):
        """Show settings menu"""
        logger.info("Showing settings screen")
        bt_settings = BluetoothSettingsScreen(self.stdscr)
        self.current_screen = bt_settings
        bt_settings.draw()

        while self.running:
            # Check for now playing combo
            if self.should_return_to_now_playing:
                self.should_return_to_now_playing = False
                self.show_now_playing()
                # Restore current_screen to bt_settings after returning
                self.current_screen = bt_settings
                bt_settings.draw()
                continue

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
                logger.info("Exiting settings screen")
                break

            bt_settings.draw()

    def show_artists(self):
        """Show artists browser"""
        # Use cached artists if available, otherwise fetch from Navidrome
        if self.cached_artists is None:
            logger.info("Fetching artists from Navidrome")
            artists = self.client.get_artists()
            self.cached_artists = artists
            logger.info(f"Cached {len(artists)} artists")
        else:
            logger.debug("Using cached artists")
            artists = self.cached_artists

        if not artists:
            logger.warning("No artists found")
            return

        browser = ArtistBrowserScreen(self.stdscr, artists)
        self.current_screen = browser
        browser.draw()

        while self.running:
            # Check for now playing combo
            if self.should_return_to_now_playing:
                self.should_return_to_now_playing = False
                self.show_now_playing()
                self.current_screen = browser
                browser.draw()
                continue

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
                logger.info("Returning to main menu from artists")
                break
            elif isinstance(result, tuple):
                action, data = result
                if action == "select_artist":
                    logger.info(f"Artist selected: {data.get('name', 'Unknown')}")
                    # Show artist's albums
                    self.show_artist_albums(data)
                    # Restore current_screen to browser after returning
                    self.current_screen = browser
                    browser.draw()

            browser.draw()

    def show_artist_albums(self, artist):
        """Show albums for a specific artist"""
        logger.info(f"Loading albums for artist: {artist.get('name', 'Unknown')}")
        albums = self.client.get_artist_albums(artist['id'])

        if not albums:
            logger.warning(f"No albums found for artist: {artist.get('name', 'Unknown')}")
            return

        logger.info(f"Loaded {len(albums)} albums")

        # Create album browser for this artist's albums
        browser = AlbumBrowserScreen(self.stdscr, albums)
        self.current_screen = browser
        browser.draw()

        while self.running:
            # Check for now playing combo
            if self.should_return_to_now_playing:
                self.should_return_to_now_playing = False
                self.show_now_playing()
                self.current_screen = browser
                browser.draw()
                continue

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
                logger.info("Returning to artist browser from albums")
                return  # Return to artist browser
            elif isinstance(result, tuple):
                action, data = result
                if action == "select_album":
                    logger.info(f"Album selected: {data.get('name', 'Unknown')}")
                    # Show song list screen
                    self.show_song_list(data)
                    # Restore current_screen to browser after returning from song list
                    self.current_screen = browser
                    browser.draw()

            browser.draw()

    def show_playlists(self):
        """Show playlists browser"""
        # Use cached playlists if available, otherwise fetch from Navidrome
        if self.cached_playlists is None:
            logger.info("Fetching playlists from Navidrome")
            playlists = self.client.get_playlists()
            self.cached_playlists = playlists
            logger.info(f"Cached {len(playlists)} playlists")
        else:
            logger.debug("Using cached playlists")
            playlists = self.cached_playlists

        if not playlists:
            logger.warning("No playlists found")
            return

        browser = PlaylistBrowserScreen(self.stdscr, playlists)
        self.current_screen = browser
        browser.draw()

        while self.running:
            # Check for now playing combo
            if self.should_return_to_now_playing:
                self.should_return_to_now_playing = False
                self.show_now_playing()
                self.current_screen = browser
                browser.draw()
                continue

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
                logger.info("Returning to main menu from playlists")
                break
            elif isinstance(result, tuple):
                action, data = result
                if action == "select_playlist":
                    logger.info(f"Playlist selected: {data.get('name', 'Unknown')}")
                    # Show playlist songs
                    self.show_playlist_songs(data)
                    # Restore current_screen to browser after returning
                    self.current_screen = browser
                    browser.draw()

            browser.draw()

    def show_playlist_songs(self, playlist):
        """Show songs in a playlist"""
        logger.info(f"Loading songs for playlist: {playlist.get('name', 'Unknown')}")
        songs = self.client.get_playlist_songs(playlist['id'])

        if not songs:
            logger.warning(f"No songs found in playlist: {playlist.get('name', 'Unknown')}")
            return

        logger.info(f"Loaded {len(songs)} songs")

        # Create song list screen for playlist
        song_list = SongListScreen(self.stdscr, playlist, songs)
        self.current_screen = song_list
        song_list.draw()

        while self.running:
            # Check for now playing combo
            if self.should_return_to_now_playing:
                self.should_return_to_now_playing = False
                self.show_now_playing()
                self.current_screen = song_list
                song_list.draw()
                continue

            key = self.stdscr.getch()

            result = None

            if key != -1:
                # Try button emulator first, only call handle_input if not handled
                handled_by_buttons = self._handle_keyboard_input(key)
                if not handled_by_buttons:
                    result = song_list.handle_input(key)

            # Check for button actions
            if hasattr(song_list, '_pending_action') and song_list._pending_action:
                result = song_list._pending_action
                song_list._pending_action = None

            if result == False:
                logger.info("Exiting playlist songs (returning to playlist browser)")
                return  # Return to playlist browser
            elif result == "back":
                logger.info("Back pressed in playlist songs")
                return  # Return to playlist browser
            elif isinstance(result, tuple):
                action, data = result
                if action == "play_song":
                    logger.info(f"Playing song: {data.get('title', 'Unknown')}")
                    self.play_song(data)
                    self.show_now_playing()
                    # Restore current_screen to song_list after returning
                    self.current_screen = song_list
                    song_list.draw()

            song_list.draw()

    def quit(self):
        logger.info("Quit requested")
        self.running = False

    def return_to_now_playing(self):
        """Return to now playing screen if there's active playback"""
        if self.has_active_playback:
            logger.info("Combo pressed: returning to now playing")
            self.should_return_to_now_playing = True
        else:
            logger.debug("Combo pressed but no active playback")

    def cleanup(self):
        logger.info("Cleaning up application resources")
        self.button_controller.stop()
        # Clean up current screen if it has cleanup method
        if self.current_screen and hasattr(self.current_screen, 'cleanup'):
            logger.debug(f"Cleaning up screen: {type(self.current_screen).__name__}")
            self.current_screen.cleanup()
        logger.info("Cleanup complete")

def main(stdscr):
    log_startup()
    try:
        app = MusicPlayerApp(stdscr)
        app.run()
    finally:
        log_shutdown()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        print("\nExiting...")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        raise