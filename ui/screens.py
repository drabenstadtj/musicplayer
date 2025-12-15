import curses
import unicodedata
from ui.theme import *
from player.album_art import AlbumArtDisplay
from player.bluetooth import BluetoothManager

def display_width(text):
    """Calculate the display width of a string, accounting for wide characters"""
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            width += 2  # Full-width or Wide characters
        else:
            width += 1  # Normal width
    return width

def truncate_to_width(text, max_width):
    """Truncate text to fit within max_width, accounting for wide characters"""
    if display_width(text) <= max_width:
        return text

    current_width = 0
    result = ""
    ellipsis = "..."
    ellipsis_width = display_width(ellipsis)

    for char in text:
        char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1
        if current_width + char_width + ellipsis_width > max_width:
            return result + ellipsis
        result += char
        current_width += char_width

    return result

class BaseScreen:
    """Base class for all screens"""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()
        self._pending_action = None

    def draw_status_bar(self, text, battery_percent=None):
        """Draw status bar at top"""
        self.stdscr.addstr(0, 0, " " * (self.width - 1))
        self.stdscr.addstr(0, 2, text, curses.color_pair(COLOR_STATUS) | curses.A_BOLD)

        if battery_percent is not None:
            battery_text = f"{battery_percent}% {SYMBOL_BATTERY}"
            self.stdscr.addstr(0, self.width - len(battery_text) - 2,
                             battery_text, curses.color_pair(COLOR_STATUS))

    def draw_footer(self, text):
        """Draw footer at bottom"""
        self.stdscr.addstr(self.height - 1, 0, " " * (self.width - 1))
        self.stdscr.addstr(self.height - 1, 2, text[:self.width - 4])

    def draw(self):
        """Override this in subclasses"""
        pass

    def handle_input(self, key):
        """Override this in subclasses. Return False to exit screen."""
        return True
    
    # Button methods - override in subclasses
    def on_up(self):
        """Handle UP button"""
        pass
    
    def on_down(self):
        """Handle DOWN button"""
        pass
    
    def on_select(self):
        """Handle SELECT button"""
        pass
    
    def on_back(self):
        """Handle BACK button"""
        pass


class MainMenuScreen(BaseScreen):
    """Main menu screen"""
    def __init__(self, stdscr):
        super().__init__(stdscr)
        self.menu_items = ["Albums", "Playlists", "Artists", "Settings"]
        self.selected = 0

    def draw(self):
        self.stdscr.clear()
        self.draw_status_bar(f"{SYMBOL_MUSIC} MUSIC PLAYER", battery_percent=85)

        # Draw menu items
        start_y = 3
        for i, item in enumerate(self.menu_items):
            y = start_y + (i * 2)
            if i == self.selected:
                self.stdscr.addstr(y, 8, f"> {item}",
                                 curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
            else:
                self.stdscr.addstr(y, 10, item, curses.color_pair(COLOR_NORMAL))

        self.draw_footer("↑/↓:Navigate  ENTER:Select  Q:Quit")
        self.stdscr.refresh()

    def handle_input(self, key):
        if key == curses.KEY_UP:
            self.selected = max(0, self.selected - 1)
        elif key == curses.KEY_DOWN:
            self.selected = min(len(self.menu_items) - 1, self.selected + 1)
        elif key == ord('\n'):  # Enter key
            return self.menu_items[self.selected]  # Return selected menu
        elif key == ord('q') or key == ord('Q'):
            return False
        return True
    
    # Button support
    def on_up(self):
        self.selected = max(0, self.selected - 1)
        self.draw()
    
    def on_down(self):
        self.selected = min(len(self.menu_items) - 1, self.selected + 1)
        self.draw()
    
    def on_select(self):
        self._pending_action = self.menu_items[self.selected]
    
    def on_back(self):
        # On main menu, back does nothing (use long-press to quit)
        pass


class AlbumBrowserScreen(BaseScreen):
    """Album browser screen (split view)"""
    def __init__(self, stdscr, albums):
        super().__init__(stdscr)
        self.albums = albums
        self.songs = []
        self.album_index = 0
        self.song_index = 0
        self.active_panel = "albums"  # "albums" or "songs"
        self.album_scroll_offset = 0
        self.artist_scroll_offset = 0
        self.scroll_frame = 0
        self.last_album_index = 0
        self.last_song_index = 0
        self.last_active_panel = "albums"

    def set_songs(self, songs):
        """Set songs for selected album"""
        self.songs = songs
        self.song_index = 0
        self.active_panel = "songs"

    def _get_scrolled_text(self, text, max_width, is_selected, scroll_type='album'):
        """Get scrolling text for selected items with truncated content

        Args:
            text: Text to scroll
            max_width: Maximum display width
            is_selected: Whether this item is selected
            scroll_type: 'album' or 'artist' to use appropriate scroll offset
        """
        text_width = display_width(text)

        if not is_selected or text_width <= max_width:
            # Not selected or fits within width - no scrolling needed
            return truncate_to_width(text, max_width)

        # Get and increment the appropriate scroll offset
        if scroll_type == 'album':
            self.album_scroll_offset = (self.album_scroll_offset + 1) % (text_width + 3)
            scroll_offset = self.album_scroll_offset
        else:  # artist
            self.artist_scroll_offset = (self.artist_scroll_offset + 1) % (text_width + 3)
            scroll_offset = self.artist_scroll_offset

        # Create circular scrolling effect
        # Add padding between end and start
        scrolling_text = text + "   " + text

        # Calculate starting position in the scrolling text
        start_offset = scroll_offset

        # Extract visible portion
        visible_text = ""
        current_width = 0
        char_index = 0

        # Skip to starting offset
        temp_offset = 0
        while temp_offset < start_offset and char_index < len(scrolling_text):
            char = scrolling_text[char_index]
            char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1
            temp_offset += char_width
            char_index += 1

        # Collect visible characters
        while current_width < max_width and char_index < len(scrolling_text):
            char = scrolling_text[char_index]
            char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1
            if current_width + char_width > max_width:
                break
            visible_text += char
            current_width += char_width
            char_index += 1

        return visible_text

    def draw(self):
        # Reset scroll if selection changed (check both index AND panel)
        selection_changed = (
            self.album_index != self.last_album_index or
            self.song_index != self.last_song_index or
            self.active_panel != self.last_active_panel
        )

        if selection_changed:
            self.album_scroll_offset = 0
            self.artist_scroll_offset = 0
            self.scroll_frame = 0
            self.last_album_index = self.album_index
            self.last_song_index = self.song_index
            self.last_active_panel = self.active_panel

        self.stdscr.clear()
        self.draw_status_bar("Albums", battery_percent=85)

        # Split screen in half
        mid_x = self.width // 2

        # Draw albums (left panel)
        self.stdscr.addstr(2, 2, "Albums:", curses.A_BOLD)
        start = max(0, self.album_index - 5)
        for i in range(start, min(len(self.albums), start + 10)):
            y = 4 + (i - start)
            if y >= self.height - 2:
                break

            # Format album display with right-justified artist
            album = self.albums[i]
            artist = album.get('artist', 'Unknown Artist')
            album_name = album['name']

            # Calculate available space
            is_selected = i == self.album_index and self.active_panel == "albums"
            prefix = "> " if is_selected else "  "
            x_start = 2

            # Calculate max width for content (accounting for display width, not string length)
            # From x_start to separator (mid_x), leave 1 char margin before separator
            max_line_width = mid_x - x_start - 1 - display_width(prefix)

            # Reserve minimum space for album and artist (with reasonable split)
            # Use 60% for album, 40% for artist
            max_artist_width = int(max_line_width * 0.4)
            album_width = max_line_width - max_artist_width - 1

            # Scroll album and artist separately if selected and truncated
            if is_selected:
                # Check if album needs scrolling
                if display_width(album_name) > album_width:
                    album_display = self._get_scrolled_text(album_name, album_width, True, 'album')
                else:
                    album_display = truncate_to_width(album_name, album_width)

                # Check if artist needs scrolling
                if display_width(artist) > max_artist_width:
                    artist_display = self._get_scrolled_text(artist, max_artist_width, True, 'artist')
                else:
                    artist_display = truncate_to_width(artist, max_artist_width)

                album_display_width = display_width(album_display)
                artist_width = display_width(artist_display)
            else:
                # Not selected - just truncate
                artist_display = truncate_to_width(artist, max_artist_width)
                artist_width = display_width(artist_display)

                album_display = truncate_to_width(album_name, album_width)
                album_display_width = display_width(album_display)

            # Calculate padding needed (in spaces, which are always width 1)
            padding_needed = max_line_width - album_display_width - artist_width - 1
            if padding_needed < 0:
                padding_needed = 0

            album_padded = album_display + (" " * padding_needed)
            display_text = f"{album_padded} {artist_display}"

            # Final safety check - ensure total display width doesn't exceed limit
            text_display_width = display_width(display_text)
            if text_display_width > max_line_width:
                display_text = truncate_to_width(display_text, max_line_width)

            if is_selected:
                self.stdscr.addstr(y, x_start, f"{prefix}{display_text}",
                                 curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
            else:
                self.stdscr.addstr(y, x_start, f"{prefix}{display_text}",
                                 curses.color_pair(COLOR_NORMAL))

        # Draw vertical separator
        for y in range(2, self.height - 1):
            self.stdscr.addstr(y, mid_x, "│")

        # Draw songs (right panel)
        if self.songs:
            self.stdscr.addstr(2, mid_x + 2, "Songs:", curses.A_BOLD)
            start = max(0, self.song_index - 5)
            for i in range(start, min(len(self.songs), start + 10)):
                y = 4 + (i - start)
                if y >= self.height - 2:
                    break

                # Format: "Track# - Song Title - Artist"
                song = self.songs[i]
                track_num = song.get('track', '')
                title = song.get('title', 'Unknown')
                artist = song.get('artist', 'Unknown Artist')

                # Build display text with track number if available
                if track_num:
                    display_text = f"{track_num}. {title} - {artist}"
                else:
                    display_text = f"{title} - {artist}"

                # Truncate to fit panel width
                max_width = mid_x - 6
                if len(display_text) > max_width:
                    display_text = display_text[:max_width - 3] + "..."

                if i == self.song_index and self.active_panel == "songs":
                    self.stdscr.addstr(y, mid_x + 2, f"> {display_text}",
                                     curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
                else:
                    self.stdscr.addstr(y, mid_x + 4, display_text,
                                     curses.color_pair(COLOR_NORMAL))

        self.draw_footer("↑/↓:Navigate  ENTER:Select  BACKSPACE:Back")
        self.stdscr.refresh()

    def handle_input(self, key):
        if key == curses.KEY_UP:
            if self.active_panel == "albums":
                self.album_index = max(0, self.album_index - 1)
            else:
                self.song_index = max(0, self.song_index - 1)

        elif key == curses.KEY_DOWN:
            if self.active_panel == "albums":
                self.album_index = min(len(self.albums) - 1, self.album_index + 1)
            elif self.songs:
                self.song_index = min(len(self.songs) - 1, self.song_index + 1)

        elif key == ord('\n'):  # Enter
            if self.active_panel == "albums":
                return ("load_album", self.albums[self.album_index]['id'])
            else:
                return ("play_song", self.songs[self.song_index])

        elif key == curses.KEY_BACKSPACE or key == 127:
            if self.active_panel == "songs":
                self.songs = []
                self.active_panel = "albums"
            else:
                return "back"

        elif key == ord('q') or key == ord('Q'):
            return False

        return True
    
    # Button support
    def on_up(self):
        if self.active_panel == "albums":
            self.album_index = max(0, self.album_index - 1)
        else:
            self.song_index = max(0, self.song_index - 1)
        self.draw()
    
    def on_down(self):
        if self.active_panel == "albums":
            self.album_index = min(len(self.albums) - 1, self.album_index + 1)
        elif self.songs:
            self.song_index = min(len(self.songs) - 1, self.song_index + 1)
        self.draw()
    
    def on_select(self):
        if self.active_panel == "albums":
            self._pending_action = ("load_album", self.albums[self.album_index]['id'])
        else:
            self._pending_action = ("play_song", self.songs[self.song_index])
    
    def on_back(self):
        if self.active_panel == "songs":
            self.songs = []
            self.active_panel = "albums"
            self.draw()
        else:
            self._pending_action = "back"


class NowPlayingScreen(BaseScreen):
    """Now playing screen"""
    def __init__(self, stdscr, audio_player, navidrome_client=None):
        super().__init__(stdscr)
        self.player = audio_player
        self.client = navidrome_client
        self.album_art = AlbumArtDisplay()
        self.current_art_path = None
        self.last_song_id = None  # Track which song we downloaded art for

    def draw(self):
        self.stdscr.clear()
        self.draw_status_bar("Now Playing", battery_percent=85)

        if self.player.current_song:
            song = self.player.current_song

            title = song.get('title', 'Unknown')
            artist = song.get('artist', 'Unknown Artist')
            album = song.get('album', 'Unknown Album')

            # Download album art only once per song
            song_id = song.get('id')
            if self.client and song_id and song_id != self.last_song_id:
                # Try different fields that might contain cover art ID
                cover_art_id = song.get('coverArt') or song.get('albumId') or song_id
                if cover_art_id:
                    try:
                        cover_art_url = self.client.get_cover_art_url(cover_art_id, size=200)
                        if cover_art_url:
                            # Download and cache the album art
                            art_path = self.album_art.download_cover_art(cover_art_url, cover_art_id)
                            if art_path:
                                self.current_art_path = art_path
                    except Exception as e:
                        # Silently fail - album art is optional
                        pass
                    finally:
                        self.last_song_id = song_id

            # Display album art on the left side if available
            art_width = 40
            art_height = 20
            info_x_offset = 2

            if self.current_art_path:
                # Display ASCII art
                art_lines = self.album_art.get_ascii_art(self.current_art_path, art_width, art_height)
                start_y = 3
                for i, line in enumerate(art_lines):
                    if start_y + i >= self.height - 2:
                        break
                    try:
                        # Truncate line to fit width
                        display_line = line[:art_width] if len(line) > art_width else line
                        self.stdscr.addstr(start_y + i, info_x_offset, display_line)
                    except:
                        pass  # Skip lines that don't fit

                # Song info on the right side of album art
                info_x_offset = art_width + 4

            # Song info
            info_y = 3
            max_text_width = self.width - info_x_offset - 2

            self.stdscr.addstr(info_y, info_x_offset, "Title:", curses.A_BOLD)
            self.stdscr.addstr(info_y + 1, info_x_offset, truncate_to_width(title, max_text_width),
                             curses.color_pair(COLOR_PLAYING))

            self.stdscr.addstr(info_y + 3, info_x_offset, "Artist:", curses.A_BOLD)
            self.stdscr.addstr(info_y + 4, info_x_offset, truncate_to_width(artist, max_text_width))

            self.stdscr.addstr(info_y + 6, info_x_offset, "Album:", curses.A_BOLD)
            self.stdscr.addstr(info_y + 7, info_x_offset, truncate_to_width(album, max_text_width))

            # Status
            status = f"{SYMBOL_PLAYING} PLAYING" if not self.player.is_paused else f"{SYMBOL_PAUSED} PAUSED"
            self.stdscr.addstr(info_y + 10, info_x_offset, status,
                             curses.color_pair(COLOR_PLAYING) | curses.A_BOLD)

            # Volume
            vol_percent = int(self.player.volume * 100)
            self.stdscr.addstr(info_y + 11, info_x_offset, f"Volume: {vol_percent}%")
        else:
            self.stdscr.addstr(self.height // 2, 2, "No song playing")

        self.draw_footer("SPACE:Play/Pause  ↑/↓:Volume  BACKSPACE:Back  Q:Quit")
        self.stdscr.refresh()

    def handle_input(self, key):
        if key == ord(' '):  # Spacebar
            self.player.toggle_pause()
        elif key == curses.KEY_UP:
            self.player.volume_up(0.1)
        elif key == curses.KEY_DOWN:
            self.player.volume_down(0.1)
        elif key == curses.KEY_BACKSPACE or key == 127:
            return "back"
        elif key == ord('q') or key == ord('Q'):
            return False
        return True
    
    # Button support
    def on_up(self):
        self.player.volume_up(0.1)
        self.draw()
    
    def on_down(self):
        self.player.volume_down(0.1)
        self.draw()
    
    def on_select(self):
        self.player.toggle_pause()
        self.draw()
    
    def on_back(self):
        self._pending_action = "back"

    def cleanup(self):
        """Clean up album art temporary files"""
        if self.album_art:
            self.album_art.cleanup()


class BluetoothSettingsScreen(BaseScreen):
    """Bluetooth audio settings screen"""
    def __init__(self, stdscr):
        super().__init__(stdscr)
        self.bt = BluetoothManager()
        self.devices = []
        self.selected = 0
        self.scanning = False
        self.status_message = ""
        self.connected_device = None
        self._refresh_devices()

    def _refresh_devices(self):
        """Refresh the device list"""
        if not self.bt.bluetoothctl_available:
            self.status_message = "Bluetooth not available"
            return

        # Get connected devices
        connected = self.bt.get_connected_devices()
        if connected:
            self.connected_device = connected[0]  # First connected device

        # Get all known devices
        self.devices = self.bt.scan_devices(duration=0)  # Quick list of known devices
        self.selected = min(self.selected, max(0, len(self.devices) - 1))

    def draw(self):
        self.stdscr.clear()
        self.draw_status_bar("Bluetooth Audio", battery_percent=85)

        if not self.bt.bluetoothctl_available:
            self.stdscr.addstr(3, 2, "Bluetooth not available on this system", curses.A_BOLD)
            self.draw_footer("BACKSPACE:Back  Q:Quit")
            self.stdscr.refresh()
            return

        # Show connected device
        y = 3
        if self.connected_device:
            mac, name = self.connected_device
            self.stdscr.addstr(y, 2, "Connected:", curses.A_BOLD)
            self.stdscr.addstr(y, 14, f"{name}", curses.color_pair(COLOR_PLAYING))
            y += 1
            self.stdscr.addstr(y, 2, f"({mac})", curses.color_pair(COLOR_NORMAL) | curses.A_DIM)
            y += 2
        else:
            self.stdscr.addstr(y, 2, "Not connected to any device", curses.A_DIM)
            y += 2

        # Status message
        if self.status_message:
            self.stdscr.addstr(y, 2, self.status_message, curses.color_pair(COLOR_PLAYING))
            y += 1

        if self.scanning:
            self.stdscr.addstr(y, 2, "Scanning for devices...", curses.A_BOLD)
            y += 2

        # Device list
        self.stdscr.addstr(y, 2, "Options:", curses.A_BOLD)
        y += 2

        # Always show "Scan for devices" as first option
        scan_selected = self.selected == 0
        scan_text = "> [Scan for devices]" if scan_selected else "  [Scan for devices]"
        if scan_selected:
            self.stdscr.addstr(y, 4, scan_text, curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
        else:
            self.stdscr.addstr(y, 4, scan_text, curses.color_pair(COLOR_NORMAL))
        y += 1

        # Show connected device disconnect option if connected
        if self.connected_device:
            disconnect_selected = self.selected == 1
            mac, name = self.connected_device
            disconnect_text = f"> [Disconnect {name}]" if disconnect_selected else f"  [Disconnect {name}]"
            if disconnect_selected:
                self.stdscr.addstr(y, 4, truncate_to_width(disconnect_text, self.width - 6),
                                 curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
            else:
                self.stdscr.addstr(y, 4, truncate_to_width(disconnect_text, self.width - 6),
                                 curses.color_pair(COLOR_NORMAL))
            y += 1

        y += 1
        if self.devices:
            self.stdscr.addstr(y, 2, "Devices:", curses.A_BOLD)
            y += 1

        # Calculate offset for device list items
        device_offset = 2 if self.connected_device else 1

        if self.devices:
            for i, (mac, name, paired) in enumerate(self.devices):
                if y >= self.height - 3:
                    break

                list_index = i + device_offset
                is_selected = list_index == self.selected
                prefix = "> " if is_selected else "  "

                # Show device name
                status = ""
                if self.bt.is_connected(mac):
                    status = " [CONNECTED]"
                    color = COLOR_PLAYING
                elif paired:
                    status = " [PAIRED]"
                    color = COLOR_SELECTED
                else:
                    color = COLOR_NORMAL

                display_text = f"{prefix}{name}{status}"
                max_width = self.width - 6

                if is_selected:
                    self.stdscr.addstr(y, 4, truncate_to_width(display_text, max_width),
                                     curses.color_pair(COLOR_SELECTED) | curses.A_BOLD)
                else:
                    self.stdscr.addstr(y, 4, truncate_to_width(display_text, max_width),
                                     curses.color_pair(color))

                y += 1

        self.draw_footer("↑/↓:Navigate  SELECT:Choose  BACK:Return")
        self.stdscr.refresh()

    def handle_input(self, key):
        # Calculate max selection index
        device_offset = 2 if self.connected_device else 1
        max_selection = len(self.devices) + device_offset - 1

        if key == curses.KEY_UP:
            self.selected = max(0, self.selected - 1)

        elif key == curses.KEY_DOWN:
            self.selected = min(max_selection, self.selected + 1)

        elif key == ord('\n'):  # Enter/SELECT button
            if self.selected == 0:
                # Scan for devices option
                self.scanning = True
                self.status_message = "Scanning..."
                self.draw()
                self.stdscr.refresh()

                self.devices = self.bt.scan_devices(duration=5)
                self.scanning = False
                self.status_message = f"Found {len(self.devices)} device(s)"
                self._refresh_devices()

            elif self.connected_device and self.selected == 1:
                # Disconnect option
                mac, name = self.connected_device
                self.status_message = f"Disconnecting from {name}..."
                self.draw()
                self.stdscr.refresh()

                if self.bt.disconnect_device(mac):
                    self.status_message = "Disconnected"
                    self.connected_device = None
                else:
                    self.status_message = "Failed to disconnect"
                self._refresh_devices()

            else:
                # Connect to a device
                device_index = self.selected - device_offset
                if 0 <= device_index < len(self.devices):
                    mac, name, paired = self.devices[device_index]

                    self.status_message = f"Connecting to {name}..."
                    self.draw()
                    self.stdscr.refresh()

                    # Pair if not paired
                    if not paired:
                        self.status_message = "Pairing..."
                        self.draw()
                        self.stdscr.refresh()

                        if not self.bt.pair_device(mac):
                            self.status_message = "Pairing failed"
                            return True

                    # Connect
                    if self.bt.connect_device(mac):
                        self.status_message = f"Connected to {name}"
                        self.connected_device = (mac, name)

                        # Set as default audio sink
                        self.bt.set_as_default_sink()
                    else:
                        self.status_message = "Connection failed"

                    self._refresh_devices()

        elif key == curses.KEY_BACKSPACE or key == 127:
            return "back"

        elif key == ord('q') or key == ord('Q'):
            return False

        return True

    # Button support
    def on_up(self):
        # UP button: Navigate up
        self.handle_input(curses.KEY_UP)
        self.draw()

    def on_down(self):
        # DOWN button: Navigate down
        self.handle_input(curses.KEY_DOWN)
        self.draw()

    def on_select(self):
        # SELECT button: Choose selected option (scan/disconnect/connect)
        self.handle_input(ord('\n'))
        self.draw()

    def on_back(self):
        self._pending_action = "back"