import requests
from requests.auth import HTTPBasicAuth
import hashlib
import random
import string

# Your config
url = "https://listen.wintermute.lol"
username = "jack"
password = "crypt0"

# Generate salt and token (Subsonic authentication)
salt = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
token = hashlib.md5((password + salt).encode()).hexdigest()

# Test ping endpoint
ping_url = f"{url}/rest/ping"
params = {
    'u': username,
    't': token,
    's': salt,
    'v': '1.16.1',
    'c': 'MusicPlayer',
    'f': 'json'
}

print(f"Testing: {ping_url}")
print(f"With params: u={username}, v=1.16.1, c=MusicPlayer\n")

try:
    response = requests.get(ping_url, params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('subsonic-response', {}).get('status') == 'ok':
            print("\n✓ Connection successful!")
        else:
            print(f"\n✗ Error: {data}")
    
except requests.exceptions.Timeout:
    print("✗ Connection timed out")
except Exception as e:
    print(f"✗ Error: {e}")
