"""
Local Music Library Scanner
Scans a directory for music files and extracts metadata
"""

import os
from pathlib import Path
try:
    from mutagen.mp3 import MP3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("mutagen not available - install with: pip install mutagen")


class LocalLibrary:
    """Manages local music files"""
    
    SUPPORTED_FORMATS = {'.mp3', '.flac', '.m4a', '.ogg', '.opus', '.wav'}
    
    def __init__(self, music_dir="/home/jack/"):
        """
        Initialize local library scanner
        
        Args:
            music_dir: Path to music directory
        """
        self.music_dir = Path(music_dir)
        self.songs = []
        self.albums = {}
        self.artists = {}
    
    def scan(self):
        """Scan music directory for files"""
        print(f"Scanning {self.music_dir}...")
        self.songs = []
        
        if not self.music_dir.exists():
            print(f"Music directory not found: {self.music_dir}")
            return
        
        # Find all music files
        for ext in self.SUPPORTED_FORMATS:
            for filepath in self.music_dir.rglob(f"*{ext}"):
                song_info = self._get_file_info(filepath)
                if song_info:
                    self.songs.append(song_info)
        
        print(f"Found {len(self.songs)} songs")
        
        # Organize by album and artist
        self._organize()
    
    def _get_file_info(self, filepath):
        """Extract metadata from music file"""
        try:
            song_info = {
                'path': str(filepath),
                'filename': filepath.name,
                'title': filepath.stem,  # Default to filename
                'artist': 'Unknown Artist',
                'album': 'Unknown Album',
                'track': 0,
                'duration': 0
            }
            
            if not MUTAGEN_AVAILABLE:
                return song_info
            
            # Try to read tags
            audio = None
            ext = filepath.suffix.lower()
            
            if ext == '.mp3':
                audio = MP3(filepath)
                if audio.tags:
                    song_info['title'] = str(audio.tags.get('TIT2', [filepath.stem])[0])
                    song_info['artist'] = str(audio.tags.get('TPE1', ['Unknown Artist'])[0])
                    song_info['album'] = str(audio.tags.get('TALB', ['Unknown Album'])[0])
                    track = audio.tags.get('TRCK', ['0'])[0]
                    song_info['track'] = int(str(track).split('/')[0]) if track else 0
            
            elif ext == '.flac':
                audio = FLAC(filepath)
                song_info['title'] = audio.get('title', [filepath.stem])[0]
                song_info['artist'] = audio.get('artist', ['Unknown Artist'])[0]
                song_info['album'] = audio.get('album', ['Unknown Album'])[0]
                track = audio.get('tracknumber', ['0'])[0]
                song_info['track'] = int(str(track).split('/')[0]) if track else 0
            
            elif ext == '.m4a':
                audio = MP4(filepath)
                song_info['title'] = audio.tags.get('\xa9nam', [filepath.stem])[0]
                song_info['artist'] = audio.tags.get('\xa9ART', ['Unknown Artist'])[0]
                song_info['album'] = audio.tags.get('\xa9alb', ['Unknown Album'])[0]
                track = audio.tags.get('trkn', [(0,)])[0]
                song_info['track'] = track[0] if track else 0
            
            elif ext in ['.ogg', '.opus']:
                audio = OggVorbis(filepath)
                song_info['title'] = audio.get('title', [filepath.stem])[0]
                song_info['artist'] = audio.get('artist', ['Unknown Artist'])[0]
                song_info['album'] = audio.get('album', ['Unknown Album'])[0]
                track = audio.get('tracknumber', ['0'])[0]
                song_info['track'] = int(str(track).split('/')[0]) if track else 0
            
            if audio:
                song_info['duration'] = int(audio.info.length)
            
            return song_info
            
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None
    
    def _organize(self):
        """Organize songs by album and artist"""
        self.albums = {}
        self.artists = {}
        
        for song in self.songs:
            # Group by album
            album_name = song['album']
            if album_name not in self.albums:
                self.albums[album_name] = {
                    'name': album_name,
                    'artist': song['artist'],
                    'songs': []
                }
            self.albums[album_name]['songs'].append(song)
            
            # Group by artist
            artist_name = song['artist']
            if artist_name not in self.artists:
                self.artists[artist_name] = {
                    'name': artist_name,
                    'albums': set(),
                    'songs': []
                }
            self.artists[artist_name]['albums'].add(album_name)
            self.artists[artist_name]['songs'].append(song)
        
        # Sort songs within albums by track number
        for album in self.albums.values():
            album['songs'].sort(key=lambda s: s['track'])
    
    def get_albums(self):
        """Get list of albums sorted by name"""
        albums = [
            {
                'id': name,
                'name': name,
                'artist': info['artist'],
                'song_count': len(info['songs'])
            }
            for name, info in self.albums.items()
        ]
        return sorted(albums, key=lambda a: a['name'])
    
    def get_album_songs(self, album_id):
        """Get songs in an album"""
        if album_id in self.albums:
            return self.albums[album_id]['songs']
        return []
    
    def get_artists(self):
        """Get list of artists"""
        artists = [
            {
                'id': name,
                'name': name,
                'album_count': len(info['albums']),
                'song_count': len(info['songs'])
            }
            for name, info in self.artists.items()
        ]
        return sorted(artists, key=lambda a: a['name'])


if __name__ == "__main__":
    # Test the library scanner
    library = LocalLibrary()
    library.scan()
    
    print("\n=== Albums ===")
    for album in library.get_albums()[:10]:
        print(f"{album['name']} - {album['artist']} ({album['song_count']} songs)")
    
    print("\n=== Artists ===")
    for artist in library.get_artists()[:10]:
        print(f"{artist['name']} ({artist['album_count']} albums, {artist['song_count']} songs)")   