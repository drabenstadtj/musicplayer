from player.navidrome import NavidromeClient

client = NavidromeClient()

print("Fetching albums...")
albums = client.get_albums(limit=500)

print(f"\nTotal albums fetched: {len(albums)}")

if albums:
    print("\nFirst 5 albums:")
    for i, album in enumerate(albums[:5]):
        print(f"  {i+1}. {album['name']} by {album.get('artist', 'Unknown')}")

    print("\nLast 5 albums:")
    for i, album in enumerate(albums[-5:]):
        print(f"  {len(albums)-4+i}. {album['name']} by {album.get('artist', 'Unknown')}")

    # Check alphabetical distribution
    first_letters = {}
    for album in albums:
        first_letter = album['name'][0].upper() if album['name'] else '?'
        first_letters[first_letter] = first_letters.get(first_letter, 0) + 1

    print("\nAlbums by first letter:")
    for letter in sorted(first_letters.keys()):
        print(f"  {letter}: {first_letters[letter]} albums")
