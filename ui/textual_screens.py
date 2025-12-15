"""Textual-based UI screens (modern alternative to curses)"""
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static, Label, ProgressBar
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.console import Group
from PIL import Image
import io
import requests


class AlbumArtWidget(Static):
    """Widget to display album art using Rich/Pillow"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.art_url = None
        self._image_data = None

    async def load_art(self, url):
        """Download and display album art"""
        if url == self.art_url:
            return

        self.art_url = url

        try:
            # Download image
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            # Load with PIL
            img = Image.open(io.BytesIO(response.content))

            # Resize to reasonable terminal size (roughly 40x20 characters)
            # Each character is roughly 2:1 ratio (height:width)
            img.thumbnail((80, 40))

            # Convert to ASCII art representation
            self._image_data = self._image_to_rich(img)
            self.update(self._image_data)

        except Exception as e:
            self.update(f"[dim]Album art unavailable[/dim]")

    def _image_to_rich(self, img):
        """Convert PIL image to Rich renderable"""
        # For now, show a placeholder
        # In production, you could use rich-pixels or similar
        width, height = img.size
        return Panel(
            f"[dim]Album Art\n{width}x{height}[/dim]",
            title="Cover",
            border_style="blue"
        )


class SongInfoWidget(Static):
    """Widget to display song information"""

    title = reactive("Unknown")
    artist = reactive("Unknown Artist")
    album = reactive("Unknown Album")

    def render(self):
        """Render song information"""
        text = Text()
        text.append("Title: ", style="bold cyan")
        text.append(f"{self.title}\n\n", style="white")
        text.append("Artist: ", style="bold cyan")
        text.append(f"{self.artist}\n\n", style="white")
        text.append("Album: ", style="bold cyan")
        text.append(f"{self.album}", style="white")

        return Panel(text, title="Now Playing", border_style="green")


class PlaybackControlsWidget(Static):
    """Widget to display playback controls and status"""

    is_playing = reactive(False)
    is_paused = reactive(False)
    volume = reactive(70)
    position = reactive(0)
    duration = reactive(0)

    def render(self):
        """Render playback controls"""
        # Status icon
        if self.is_paused:
            status = "⏸  PAUSED"
            style = "yellow bold"
        elif self.is_playing:
            status = "▶  PLAYING"
            style = "green bold"
        else:
            status = "⏹  STOPPED"
            style = "dim"

        text = Text()
        text.append(status + "\n\n", style=style)
        text.append(f"Volume: {self.volume}%\n", style="white")

        # Progress bar representation
        if self.duration > 0:
            progress = int((self.position / self.duration) * 30)
            bar = "█" * progress + "░" * (30 - progress)
            time_str = f"{self._format_time(self.position)} / {self._format_time(self.duration)}"
            text.append(f"\n{bar}\n{time_str}", style="cyan")

        return Panel(text, title="Controls", border_style="magenta")

    def _format_time(self, seconds):
        """Format seconds as MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"


class TextualNowPlayingScreen(Screen):
    """Now Playing screen using Textual"""

    BINDINGS = [
        ("space", "toggle_pause", "Play/Pause"),
        ("up", "volume_up", "Volume Up"),
        ("down", "volume_down", "Volume Down"),
        ("escape", "back", "Back"),
        ("q", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    #content {
        height: 1fr;
    }

    #left-panel {
        width: 50%;
        height: 100%;
    }

    #right-panel {
        width: 50%;
        height: 100%;
        padding-left: 2;
    }

    #footer {
        height: 3;
        dock: bottom;
        background: $primary-darken-2;
        color: $text;
        padding: 1;
    }

    AlbumArtWidget {
        height: 100%;
    }

    SongInfoWidget {
        height: 2fr;
    }

    PlaybackControlsWidget {
        height: 1fr;
        margin-top: 1;
    }
    """

    def __init__(self, audio_player, navidrome_client=None):
        super().__init__()
        self.player = audio_player
        self.client = navidrome_client
        self.album_art_widget = None
        self.song_info_widget = None
        self.controls_widget = None

    def compose(self) -> ComposeResult:
        """Compose the UI"""
        with Container(id="main-container"):
            with Horizontal(id="content"):
                with Vertical(id="left-panel"):
                    self.album_art_widget = AlbumArtWidget()
                    yield self.album_art_widget

                with Vertical(id="right-panel"):
                    self.song_info_widget = SongInfoWidget()
                    yield self.song_info_widget

                    self.controls_widget = PlaybackControlsWidget()
                    yield self.controls_widget

            yield Label(
                "SPACE: Play/Pause  ↑/↓: Volume  ESC: Back  Q: Quit",
                id="footer"
            )

    def on_mount(self):
        """Called when screen is mounted"""
        # Update display with current song
        self.update_display()

        # Set up a timer to update playback status
        self.set_interval(0.1, self.update_display)

    def update_display(self):
        """Update the display with current playback info"""
        if not self.player.current_song:
            return

        song = self.player.current_song

        # Update song info
        if self.song_info_widget:
            self.song_info_widget.title = song.get('title', 'Unknown')
            self.song_info_widget.artist = song.get('artist', 'Unknown Artist')
            self.song_info_widget.album = song.get('album', 'Unknown Album')

        # Update controls
        if self.controls_widget:
            self.controls_widget.is_playing = self.player.is_playing
            self.controls_widget.is_paused = self.player.is_paused
            self.controls_widget.volume = int(self.player.volume * 100)
            self.controls_widget.position = self.player.get_position() if hasattr(self.player, 'get_position') else 0
            self.controls_widget.duration = song.get('duration', 0)

        # Load album art if available
        if self.client and self.album_art_widget:
            cover_art_id = song.get('coverArt') or song.get('albumId') or song.get('id')
            if cover_art_id:
                cover_url = self.client.get_cover_art_url(cover_art_id, size=300)
                if cover_url:
                    self.run_worker(self.album_art_widget.load_art(cover_url))

    def action_toggle_pause(self):
        """Toggle play/pause"""
        self.player.toggle_pause()
        self.update_display()

    def action_volume_up(self):
        """Increase volume"""
        self.player.volume_up(0.1)
        self.update_display()

    def action_volume_down(self):
        """Decrease volume"""
        self.player.volume_down(0.1)
        self.update_display()

    def action_back(self):
        """Go back to previous screen"""
        self.app.pop_screen()

    def action_quit(self):
        """Quit the app"""
        self.app.exit()
