import requests
import hashlib
import random
import string
import config

class NavidromeClient:
    def __init__(self):
        self.base_url = config.NAVIDROME_URL
        self.username = config.NAVIDROME_USER
        self.password = config.NAVIDROME_PASS
        self.api_version = '1.16.1'
        self.client_name = 'MusicPlayer'
    
    def _make_request(self, endpoint, params=None):
        """Make authenticated request to Navidrome"""
        if params is None:
            params = {}
        
        # Generate authentication token
        salt = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        token = hashlib.md5((self.password + salt).encode()).hexdigest()
        
        # Add required params
        params.update({
            'u': self.username,
            't': token,
            's': salt,
            'v': self.api_version,
            'c': self.client_name,
            'f': 'json'
        })
        
        url = f"{self.base_url}/rest/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for Subsonic API errors
            subsonic_response = data.get('subsonic-response', {})
            if subsonic_response.get('status') == 'failed':
                error = subsonic_response.get('error', {})
                raise Exception(f"API Error: {error.get('message', 'Unknown error')}")
            
            return subsonic_response
        
        except requests.exceptions.Timeout:
            raise Exception("Request timed out")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def test_connection(self):
        """Test if we can connect to Navidrome"""
        try:
            response = self._make_request('ping')
            return response.get('status') == 'ok'
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def get_albums(self, limit=100):
        """Get list of albums"""
        try:
            response = self._make_request('getAlbumList2', {
                'type': 'alphabeticalByName',
                'size': limit
            })
            return response.get('albumList2', {}).get('album', [])
        except Exception as e:
            print(f"Error fetching albums: {e}")
            return []
    
    def get_playlists(self):
        """Get list of playlists"""
        try:
            response = self._make_request('getPlaylists')
            return response.get('playlists', {}).get('playlist', [])
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            return []
    
    def get_album_songs(self, album_id):
        """Get songs for a specific album"""
        try:
            response = self._make_request('getAlbum', {'id': album_id})
            return response.get('album', {}).get('song', [])
        except Exception as e:
            print(f"Error fetching album songs: {e}")
            return []
    
    def get_playlist_songs(self, playlist_id):
        """Get songs in a playlist"""
        try:
            response = self._make_request('getPlaylist', {'id': playlist_id})
            return response.get('playlist', {}).get('entry', [])
        except Exception as e:
            print(f"Error fetching playlist songs: {e}")
            return []
    
    def get_stream_url(self, song_id):
        """Get streaming URL for a song"""
        try:
            # Generate auth params for streaming
            salt = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            token = hashlib.md5((self.password + salt).encode()).hexdigest()
            
            params = {
                'id': song_id,
                'u': self.username,
                't': token,
                's': salt,
                'v': self.api_version,
                'c': self.client_name
            }
            
            # Build URL with params
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            return f"{self.base_url}/rest/stream?{param_string}"
        
        except Exception as e:
            print(f"Error getting stream URL: {e}")
            return None
    
    def get_cover_art_url(self, cover_art_id, size=200):
        """Get cover art URL"""
        if not cover_art_id:
            return None
        try:
            # Generate auth params
            salt = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            token = hashlib.md5((self.password + salt).encode()).hexdigest()
            
            params = {
                'id': cover_art_id,
                'size': size,
                'u': self.username,
                't': token,
                's': salt,
                'v': self.api_version,
                'c': self.client_name
            }
            
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            return f"{self.base_url}/rest/getCoverArt?{param_string}"
        
        except Exception as e:
            print(f"Error getting cover art: {e}")
            return None
