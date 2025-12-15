import subprocess
import tempfile
import os
import requests
from pathlib import Path
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import ueberzug.lib.v0 as ueberzug
    UEBERZUG_AVAILABLE = True
except ImportError:
    UEBERZUG_AVAILABLE = False

class AlbumArtDisplay:
    """Display album art in terminal using chafa"""

    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.current_art_file = None
        self.chafa_available = self._check_chafa()
        self.ueberzug_canvas = None
        self.ueberzug_placement = None

    def _check_chafa(self):
        """Check if chafa is installed"""
        try:
            subprocess.run(['chafa', '--version'],
                         capture_output=True,
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def download_cover_art(self, url, album_id):
        """Download cover art from URL"""
        if not url:
            return None

        try:
            # Create temp file path
            temp_path = os.path.join(self.temp_dir, f"cover_{album_id}.jpg")

            # Download image
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            # Save to temp file
            with open(temp_path, 'wb') as f:
                f.write(response.content)

            # Clean up old cover art
            if self.current_art_file and os.path.exists(self.current_art_file):
                try:
                    os.remove(self.current_art_file)
                except:
                    pass

            self.current_art_file = temp_path
            return temp_path

        except Exception as e:
            print(f"Error downloading cover art: {e}")
            return None

    def display_in_terminal(self, image_path, width=40, height=20):
        """Display image in terminal using chafa

        Args:
            image_path: Path to image file
            width: Width in characters (default 40)
            height: Height in characters (default 20)

        Returns:
            String containing the rendered image for terminal display
        """
        if not self.chafa_available:
            return "[Album art display not available - install chafa]"

        if not image_path or not os.path.exists(image_path):
            return "[No album art available]"

        try:
            # Run chafa to convert image to terminal output
            result = subprocess.run([
                'chafa',
                '--size', f'{width}x{height}',
                '--format', 'symbols',
                '--symbols', 'block',
                '--colors', '256',  # Use 256 colors
                image_path
            ], capture_output=True, text=True, check=True)

            return result.stdout

        except subprocess.CalledProcessError as e:
            return f"[Error displaying album art: {e}]"
        except Exception as e:
            return f"[Error: {e}]"

    def get_ansi_art(self, image_path, width=40, height=20):
        """Get ANSI art as list of lines for direct curses rendering

        This is useful for integrating with curses-based UIs
        """
        output = self.display_in_terminal(image_path, width, height)
        return output.split('\n')

    def get_ascii_art(self, image_path, width=40, height=20):
        """Convert image to pure ASCII art (no ANSI codes) for curses

        Args:
            image_path: Path to image file
            width: Width in characters
            height: Height in characters

        Returns:
            List of strings representing the ASCII art
        """
        if not PIL_AVAILABLE:
            return self._create_placeholder(width, height, "PIL not installed")

        if not image_path or not os.path.exists(image_path):
            return self._create_placeholder(width, height, "No album art")

        try:
            # Open and resize image
            img = Image.open(image_path)
            img = img.convert('L')  # Convert to grayscale

            # Resize to fit ASCII dimensions
            # Each character is roughly 2:1 (height:width) so adjust accordingly
            img = img.resize((width, height), Image.Resampling.LANCZOS)

            # ASCII characters from darkest to lightest
            ascii_chars = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
            ascii_chars = ascii_chars[::-1]  # Reverse for dark backgrounds

            # Convert pixels to ASCII
            lines = []
            pixels = img.load()
            for y in range(height):
                line = ""
                for x in range(width):
                    # Get pixel brightness (0-255)
                    brightness = pixels[x, y]
                    # Map to ASCII character
                    char_index = int((brightness / 255) * (len(ascii_chars) - 1))
                    line += ascii_chars[char_index]
                lines.append(line)

            return lines

        except Exception as e:
            return self._create_placeholder(width, height, f"Error: {str(e)[:20]}")

    def _create_placeholder(self, width, height, message="Album Art"):
        """Create a simple placeholder box"""
        lines = []
        lines.append("┌" + "─" * (width - 2) + "┐")

        # Add empty lines
        for i in range(height - 2):
            if i == height // 2 - 1:
                # Center the message
                padding = (width - len(message) - 2) // 2
                line = "│" + " " * padding + message + " " * (width - len(message) - padding - 2) + "│"
                lines.append(line)
            else:
                lines.append("│" + " " * (width - 2) + "│")

        lines.append("└" + "─" * (width - 2) + "┘")
        return lines

    def init_ueberzug(self):
        """Initialize ueberzug for real image display"""
        if not UEBERZUG_AVAILABLE:
            return False

        try:
            self.ueberzug_canvas = ueberzug.Canvas()
            return True
        except Exception as e:
            return False

    def show_image_ueberzug(self, image_path, x, y, width, height):
        """Display real image using ueberzug overlay

        Args:
            image_path: Path to image file
            x: X position in terminal (characters)
            y: Y position in terminal (characters)
            width: Width in characters
            height: Height in characters
        """
        if not UEBERZUG_AVAILABLE or not self.ueberzug_canvas:
            return False

        try:
            if self.ueberzug_placement:
                # Remove old placement
                self.ueberzug_placement.visibility = ueberzug.Visibility.INVISIBLE

            # Create new placement
            self.ueberzug_placement = self.ueberzug_canvas.create_placement(
                'album_art',
                x=x, y=y,
                width=width, height=height,
                path=image_path
            )
            self.ueberzug_placement.visibility = ueberzug.Visibility.VISIBLE
            return True

        except Exception as e:
            return False

    def hide_ueberzug(self):
        """Hide the ueberzug image"""
        if self.ueberzug_placement:
            try:
                self.ueberzug_placement.visibility = ueberzug.Visibility.INVISIBLE
            except:
                pass

    def cleanup(self):
        """Clean up temporary files and ueberzug"""
        # Clean up ueberzug
        if self.ueberzug_placement:
            try:
                self.ueberzug_placement.visibility = ueberzug.Visibility.INVISIBLE
            except:
                pass

        if self.ueberzug_canvas:
            try:
                self.ueberzug_canvas.__exit__(None, None, None)
            except:
                pass

        # Clean up temp files
        if self.current_art_file and os.path.exists(self.current_art_file):
            try:
                os.remove(self.current_art_file)
            except:
                pass
