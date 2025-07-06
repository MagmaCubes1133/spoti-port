import json
from typing import List, Dict

import spotipy
from spotipy.oauth2 import SpotifyOAuth


SCOPE = "user-library-read playlist-read-private playlist-read-collaborative"


def get_spotify_client() -> spotipy.Spotify:
    """Authenticate and return a Spotify client using OAuth."""
    auth = SpotifyOAuth(scope=SCOPE, open_browser=True)
    return spotipy.Spotify(auth_manager=auth)


def export_liked_tracks(sp: spotipy.Spotify) -> List[Dict]:
    """Return a list of liked tracks with relevant metadata."""
    items = []
    results = sp.current_user_saved_tracks(limit=50)
    while results:
        for item in results["items"]:
            track = item["track"]
            items.append({
                "name": track["name"],
                "artists": ", ".join(a["name"] for a in track["artists"]),
                "duration_ms": track["duration_ms"],
                "id": track["id"],
            })
        if results["next"]:
            results = sp.next(results)
        else:
            break
    return items


def export_playlists(sp: spotipy.Spotify) -> List[Dict]:
    """Return user's playlists with track information."""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    while results:
        for playlist in results["items"]:
            playlist_data = {
                "name": playlist["name"],
                "tracks": [],
            }
            tracks = sp.playlist_items(playlist["id"], additional_types=["track"])
            while tracks:
                for item in tracks["items"]:
                    track = item.get("track")
                    if not track:
                        continue
                    playlist_data["tracks"].append({
                        "name": track["name"],
                        "artists": ", ".join(a["name"] for a in track["artists"]),
                        "duration_ms": track["duration_ms"],
                        "id": track["id"],
                    })
                if tracks["next"]:
                    tracks = sp.next(tracks)
                else:
                    break
            playlists.append(playlist_data)
        if results["next"]:
            results = sp.next(results)
        else:
            break
    return playlists


def export_library(output_file: str = "spotify_library.json") -> None:
    """Export liked songs and playlists to a JSON file."""
    print("A browser window will open to authorize Spotify access.")
    sp = get_spotify_client()
    data = {
        "liked_songs": export_liked_tracks(sp),
        "playlists": export_playlists(sp),
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Exported library to {output_file}")


if __name__ == "__main__":
    export_library()
