import json
import html
from pathlib import Path
from typing import Dict, List

FAILED_LOG_FILE = "failed_tracks.json"

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def _decode_string(text: str) -> str:
    """Decode escaped unicode and HTML entities if present."""
    if "\\u" in text:
        try:
            text = text.encode("utf-8").decode("unicode_escape")
        except Exception:
            pass
    text = html.unescape(text)
    return text

# YouTube API scope for managing playlists
YT_SCOPE = ["https://www.googleapis.com/auth/youtube"]


def get_youtube_client() -> any:
    """Authenticate and return a YouTube API client."""
    if not Path("client_secret.json").exists():
        raise RuntimeError(
            "client_secret.json not found. Create OAuth credentials in the "
            "Google Developer Console and download the JSON file to this "
            "directory."
        )
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", YT_SCOPE)
    # Open the user's browser for a graphical login and run a local server to
    # receive the authorization code.
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)


def search_video(youtube, query: str, duration_ms: int) -> str | None:
    """Search for a YouTube video matching the query and closest in length."""
    try:
        search_response = youtube.search().list(
            q=query,
            type="video",
            part="id",
            maxResults=5,
        ).execute()
    except HttpError as err:
        print(f"YouTube search failed: {err}")
        return None

    best_video = None
    best_diff = None
    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    if not video_ids:
        return None
    details = youtube.videos().list(part="contentDetails", id=",".join(video_ids)).execute()
    for item in details.get("items", []):
        vid = item["id"]
        duration = item["contentDetails"]["duration"]
        seconds = iso8601_duration_to_seconds(duration)
        diff = abs(seconds * 1000 - duration_ms)
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_video = vid
    return best_video


def iso8601_duration_to_seconds(duration: str) -> int:
    """Convert ISO8601 duration to seconds."""
    import isodate

    td = isodate.parse_duration(duration)
    return int(td.total_seconds())


def create_playlist(youtube, title: str) -> str | None:
    """Create a new playlist and return its ID."""
    body = {
        "snippet": {"title": title},
        "status": {"privacyStatus": "private"},
    }
    try:
        response = youtube.playlists().insert(part="snippet,status", body=body).execute()
        return response["id"]
    except HttpError as err:
        print(f"Failed to create playlist: {err}")
        return None


def get_playlist_by_name(youtube, title: str) -> str | None:
    """Return playlist ID if a playlist with the given title exists."""
    page_token = None
    while True:
        response = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=page_token,
        ).execute()
        for item in response.get("items", []):
            if item["snippet"].get("title") == title:
                return item["id"]
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return None


def get_playlist_items(youtube, playlist_id: str) -> List[str]:
    """Return a list of video IDs currently in the playlist."""
    items: List[str] = []
    page_token = None
    while True:
        response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute()
        items.extend(
            entry["contentDetails"]["videoId"] for entry in response.get("items", [])
        )
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return items


def add_video_to_playlist(youtube, playlist_id: str, video_id: str) -> None:
    body = {
        "snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}
    }
    try:
        youtube.playlistItems().insert(part="snippet", body=body).execute()
    except HttpError as err:
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


def import_library(library_file: str, failed_log: str = FAILED_LOG_FILE) -> None:
    print("A browser window will open to authorize your Google account.")
    youtube = get_youtube_client()
    data = json.loads(Path(library_file).read_text())
    failed: List[Dict] = []
    for playlist in data.get("playlists", []):
        port_playlist(youtube, playlist, failed)
    if failed:
        Path(failed_log).write_text(json.dumps(failed, indent=2))
        print(f"Logged {len(failed)} unmatched tracks to {failed_log}")


if __name__ == "__main__":
    import_library("spotify_library.json")
