import json
import html
from pathlib import Path
from typing import Dict, List

FAILED_LOG_FILE = "failed_tracks.json"


from ytmusicapi import YTMusic, setup



def _decode_string(text: str) -> str:
    """Decode escaped unicode and HTML entities if present."""
    if "\\u" in text:
        try:
            text = text.encode("utf-8").decode("unicode_escape")
        except Exception:
            pass
    text = html.unescape(text)
    return text



def get_youtube_client() -> YTMusic:
    """Authenticate and return a YTMusic client using request headers."""
    headers_file = "headers_auth.json"
    if Path(headers_file).exists():
        return YTMusic(headers_file)

    print(
        "No YouTube authentication headers found. "
        "Follow the instructions to paste the headers from your browser."
    )
    setup(filepath=headers_file)
    return YTMusic(headers_file)



def search_video(youtube: YTMusic, query: str, duration_ms: int) -> str | None:
    """Search YouTube Music for the closest matching track."""
    results = youtube.search(query, filter="songs") or youtube.search(query, filter="videos")
    if not results:
        return None
    best_video = None
    best_diff = None
    for item in results[:5]:
        vid = item.get("videoId")
        dur = item.get("duration")
        if not vid or not dur:
            continue
        seconds = duration_to_seconds(dur)
        diff = abs(seconds * 1000 - duration_ms)
        if diff <= 10000:
            return vid
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_video = vid
    return best_video


def duration_to_seconds(duration: str) -> int:
    """Convert a ``MM:SS`` or ``HH:MM:SS`` duration string to seconds."""
    parts = duration.split(":")
    seconds = 0
    for p in parts:
        seconds = seconds * 60 + int(p)
    return seconds

def create_playlist(youtube: YTMusic, title: str) -> str | None:
    """Create a new playlist and return its ID."""
    try:
        return youtube.create_playlist(title, "Created by spoti-port")
    except Exception as err:
        print(f"Failed to create playlist: {err}")
        return None


def get_playlist_by_name(youtube: YTMusic, title: str) -> str | None:
    """Return playlist ID if a playlist with the given title exists."""
    playlists = youtube.get_library_playlists(limit=100)
    for pl in playlists:
        if pl.get("title") == title:
            return pl.get("playlistId")
    return None


def get_playlist_items(youtube: YTMusic, playlist_id: str) -> List[str]:
    """Return a list of video IDs currently in the playlist."""
    items: List[str] = []
    playlist = youtube.get_playlist(playlist_id, limit=10000)
    for track in playlist.get("tracks", []):
        vid = track.get("videoId")
        if vid:
            items.append(vid)
    return items


def add_video_to_playlist(youtube: YTMusic, playlist_id: str, video_id: str) -> None:
    try:
        youtube.add_playlist_items(playlist_id, [video_id])
    except Exception as err:
        print(f"Failed to add video {video_id}: {err}")


def port_playlist(youtube, playlist: Dict, failed: List[Dict]) -> None:
    yt_playlist_name = f"spoti-port-{_decode_string(playlist['name'])}"
    playlist_id = get_playlist_by_name(youtube, yt_playlist_name)
    if not playlist_id:
        playlist_id = create_playlist(youtube, yt_playlist_name)
        if not playlist_id:
            return
        existing_videos: set[str] = set()
    else:
        existing_videos = set(get_playlist_items(youtube, playlist_id))

    for track in playlist["tracks"]:
        track_name = _decode_string(track["name"])
        artists = _decode_string(track["artists"])
        query = f"{track_name} {artists}"
        video_id = search_video(youtube, query, track["duration_ms"])
        if video_id:
            if video_id not in existing_videos:
                try:
                    add_video_to_playlist(youtube, playlist_id, video_id)
                    existing_videos.add(video_id)
                except Exception:
                    failed.append({"playlist": playlist["name"], **track})
        else:
            failed.append({"playlist": playlist["name"], **track})


def _append_failed(log_file: str, failed: List[Dict]) -> None:
    """Append failed entries to the log file preserving previous data."""
    if not failed:
        return
    existing: List[Dict] = []
    if Path(log_file).exists():
        try:
            existing = json.loads(Path(log_file).read_text())
        except Exception:
            existing = []
    existing.extend(failed)
    Path(log_file).write_text(json.dumps(existing, indent=2, ensure_ascii=False))


def like_video(youtube: YTMusic, video_id: str) -> None:
    """Add the given video to the user's liked videos."""
    try:
        youtube.rate_song(video_id, "LIKE")
    except Exception as err:
        print(f"Failed to like video {video_id}: {err}")


def sync_liked_songs(youtube, tracks: List[Dict], failed: List[Dict]) -> None:
    """Sync Spotify liked songs with YouTube Music saved songs."""
    existing = set()
    try:
        existing = set(get_playlist_items(youtube, "LM"))
    except Exception:
        pass
    for track in tracks:
        track_name = _decode_string(track["name"])
        artists = _decode_string(track["artists"])
        query = f"{track_name} {artists}"
        video_id = search_video(youtube, query, track["duration_ms"])
        if video_id:
            if video_id not in existing:
                try:
                    like_video(youtube, video_id)
                    existing.add(video_id)
                except Exception:
                    failed.append({"playlist": "Liked Songs", **track})
        else:
            failed.append({"playlist": "Liked Songs", **track})


def import_library(library_file: str, failed_log: str = FAILED_LOG_FILE) -> None:
    print(
        "If this is your first run you'll be asked to provide YouTube Music "
        "authentication headers."
    )
    youtube = get_youtube_client()
    data = json.loads(Path(library_file).read_text())
    failed: List[Dict] = []

    liked_songs = data.get("liked_songs", [])
    playlists = data.get("playlists", [])
    done_liked = False
    remaining = playlists[:]

    while True:
        options: List[tuple[str, str | Dict]] = []
        if liked_songs and not done_liked:
            options.append(("Liked Songs", "liked"))
        for pl in remaining:
            options.append((_decode_string(pl["name"]), pl))
        if not options:
            break

        print("What would you like to sync?")
        print("0. Do all")
        for idx, (name, _) in enumerate(options, 1):
            print(f"{idx}. {name}")

        choice = input("Select an option number (blank to finish): ").strip()
        if not choice:
            break
        if choice == "0":
            if liked_songs and not done_liked:
                print("Syncing liked songs...")
                sync_liked_songs(youtube, liked_songs, failed)
            for pl in remaining:
                port_playlist(youtube, pl, failed)
            break
        try:
            sel = int(choice) - 1
            _, selected = options[sel]
        except (ValueError, IndexError):
            print("Invalid selection")
            continue

        if selected == "liked":
            print("Syncing liked songs...")
            sync_liked_songs(youtube, liked_songs, failed)
            done_liked = True
        else:
            port_playlist(youtube, selected, failed)
            remaining.remove(selected)

        again = input("Sync another item? [y/N]: ").strip().lower()
        if again != "y":
            break

    _append_failed(failed_log, failed)
    if failed:
        print(f"Logged {len(failed)} unmatched tracks to {failed_log}")


if __name__ == "__main__":
    import_library("spotify_library.json")
