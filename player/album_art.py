import subprocess
import tempfile
import os
import requests
from pathlib import Path

class AlbumArtDisplay:
    """Display album art in terminal using chafa"""

    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.current_art_file = None
        self.chafa_available = self._check_chafa()

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

    def cleanup(self):
        """Clean up temporary files"""
        if self.current_art_file and os.path.exists(self.current_art_file):
            try:
                os.remove(self.current_art_file)
            except:
                pass
