#!/usr/bin/env python3
"""Debug script to print song metadata"""
import json
from player.navidrome import NavidromeClient

client = NavidromeClient()

if not client.test_connection():
    print("Failed to connect to Navidrome")
    exit(1)

print("Connected to Navidrome!\n")

# Get first album
albums = client.get_albums(limit=1)
if albums:
    album = albums[0]
    print(f"Album: {album['name']}")
    print(f"Album ID: {album['id']}")
    print(f"Album metadata:")
    print(json.dumps(album, indent=2))
    print("\n" + "="*80 + "\n")

    # Get songs from that album
    songs = client.get_album_songs(album['id'])
    if songs:
        song = songs[0]
        print(f"Song: {song['title']}")
        print(f"Song metadata:")
        print(json.dumps(song, indent=2))
        print("\n" + "="*80 + "\n")

        # Try to get cover art
        cover_art_id = song.get('coverArt') or song.get('albumId') or song.get('id')
        print(f"Trying to get cover art with ID: {cover_art_id}")
        cover_url = client.get_cover_art_url(cover_art_id, size=200)
        print(f"Cover art URL: {cover_url}")
