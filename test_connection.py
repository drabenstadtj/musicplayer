from player.navidrome import NavidromeClient

print("Testing Navidrome connection...")
print("Server: https://listen.wintermute.lol")
print("User: jack\n")

try:
    client = NavidromeClient()
    
    print("Sending ping...")
    if client.test_connection():
        print("✓ Connected successfully!\n")
        
        # Test fetching albums
        print("Fetching albums...")
        albums = client.get_albums(limit=5)
        print(f"Found {len(albums)} albums:")
        for album in albums[:5]:
            print(f"  - {album['name']} by {album.get('artist', 'Unknown')}")
        
        print("\nFetching playlists...")
        playlists = client.get_playlists()
        print(f"Found {len(playlists)} playlists:")
        for playlist in playlists[:5]:
            print(f"  - {playlist['name']} ({playlist.get('songCount', 0)} songs)")
    else:
        print("✗ Connection failed")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
