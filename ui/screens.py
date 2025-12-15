import curses
import unicodedata
from ui.theme import *

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


class AlbumBrowserScreen(BaseScreen):
    """Album browser screen (split view)"""
    def __init__(self, stdscr, albums):
        super().__init__(stdscr)
        self.albums = albums
        self.songs = []
        self.album_index = 0
        self.song_index = 0
        self.active_panel = "albums"  # "albums" or "songs"
    
    def set_songs(self, songs):
        """Set songs for selected album"""
        self.songs = songs
        self.song_index = 0
        self.active_panel = "songs"
    
    def draw(self):
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

            # Truncate artist if too long (using display width)
            artist = truncate_to_width(artist, max_artist_width)
            artist_width = display_width(artist)

            # Remaining space for album (accounting for 1 space between album and artist)
            album_width = max_line_width - artist_width - 1

            # Truncate album name if needed (using display width)
            album_name = truncate_to_width(album_name, album_width)
            album_display_width = display_width(album_name)

            # Calculate padding needed (in spaces, which are always width 1)
            padding_needed = max_line_width - album_display_width - artist_width - 1
            if padding_needed < 0:
                padding_needed = 0

            album_padded = album_name + (" " * padding_needed)
            display_text = f"{album_padded} {artist}"

            # Final safety check - ensure total display width doesn't exceed limit
            text_display_width = display_width(display_text)
            if text_display_width > max_line_width:
                # Truncate more aggressively if still too long
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
    
class NowPlayingScreen(BaseScreen):
    """Now playing screen"""
    def __init__(self, stdscr, audio_player):
        super().__init__(stdscr)
        self.player = audio_player
    
    def draw(self):
        self.stdscr.clear()
        self.draw_status_bar("Now Playing", battery_percent=85)
        
        if self.player.current_song:
            song = self.player.current_song
            
            # Song info centered
            center_y = self.height // 2
            
            title = song.get('title', 'Unknown')
            artist = song.get('artist', 'Unknown Artist')
            album = song.get('album', 'Unknown Album')
            
            self.stdscr.addstr(center_y - 2, 2, "Title:", curses.A_BOLD)
            self.stdscr.addstr(center_y - 2, 10, title[:self.width - 12], 
                             curses.color_pair(COLOR_PLAYING))
            
            self.stdscr.addstr(center_y - 1, 2, "Artist:", curses.A_BOLD)
            self.stdscr.addstr(center_y - 1, 10, artist[:self.width - 12])
            
            self.stdscr.addstr(center_y, 2, "Album:", curses.A_BOLD)
            self.stdscr.addstr(center_y, 10, album[:self.width - 12])
            
            # Status
            status = f"{SYMBOL_PLAYING} PLAYING" if not self.player.is_paused else f"{SYMBOL_PAUSED} PAUSED"
            self.stdscr.addstr(center_y + 2, 2, status, 
                             curses.color_pair(COLOR_PLAYING) | curses.A_BOLD)
            
            # Volume
            vol_percent = int(self.player.volume * 100)
            self.stdscr.addstr(center_y + 3, 2, f"Volume: {vol_percent}%")
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