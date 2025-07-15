import json
import time
from pathlib import Path
from typing import List, Dict

from playwright.sync_api import sync_playwright
from ytmusicapi import YTMusic
import requests

HEADERS_FILE = "headers_auth_browser.json"
FAILED_LOG_FILE = "failed_tracks.json"


def _save_headers_from_request(headers: Dict[str, str]) -> None:
    lines = [f"{k}: {v}" for k, v in headers.items()]
    Path(HEADERS_FILE).write_text("\n".join(lines), encoding="utf-8")


def _login_and_get_headers() -> str:
    """Open a browser for the user to log in and capture request headers."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://music.youtube.com")
        print("Please log into YouTube Music in the opened window.")
        input("Press Enter here once login is complete...")
        page.reload()
        try:
            req = page.wait_for_request(
                lambda r: "browse" in r.url and "Authorization" in r.headers,
                timeout=15000,
            )
        except Exception:
            browser.close()
            raise RuntimeError("Failed to capture authenticated request")
        _save_headers_from_request(req.headers)
        browser.close()
    return HEADERS_FILE


def _get_youtube_client() -> YTMusic:
    if not Path(HEADERS_FILE).exists():
        print("Authenticating with browser...")
        _login_and_get_headers()
    return YTMusic(HEADERS_FILE)


def _rate_limit_handler(func):
    def wrapper(*args, **kwargs):
        backoff = 5
        while True:
            try:
                return func(*args, **kwargs)
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    wait = int(e.response.headers.get("Retry-After", backoff))
                    print(f"Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    backoff = min(backoff * 2, 60)
                    continue
                raise
    return wrapper


def _search_track(yt: YTMusic, query: str, duration_ms: int) -> str | None:
    results = yt.search(query, filter="songs")
    best = None
    best_diff = None
    for r in results:
        dur = r.get("duration_seconds")
        if dur is None:
            continue
        diff = abs(dur * 1000 - duration_ms)
        if best is None or diff < best_diff:
            best = r
            best_diff = diff
    return best.get("videoId") if best else None


@_rate_limit_handler
def _create_playlist(yt: YTMusic, title: str) -> str:
    return yt.create_playlist(title, "Created by spoti-port")


@_rate_limit_handler
def _add_to_playlist(yt: YTMusic, playlist_id: str, video_ids: List[str]) -> None:
    yt.add_playlist_items(playlist_id, video_ids)


@_rate_limit_handler
def _like_song(yt: YTMusic, video_id: str) -> None:
    yt.rate_song(video_id, "LIKE")


def _append_failed(failed: List[Dict]) -> None:
    if not failed:
        return
    existing: List[Dict] = []
    if Path(FAILED_LOG_FILE).exists():
        try:
            existing = json.loads(Path(FAILED_LOG_FILE).read_text())
        except Exception:
            existing = []
    existing.extend(failed)
    Path(FAILED_LOG_FILE).write_text(json.dumps(existing, indent=2, ensure_ascii=False))


def import_library(lib_file: str) -> None:
    yt = _get_youtube_client()
    data = json.loads(Path(lib_file).read_text(encoding="utf-8"))

    failed: List[Dict] = []
    liked_songs = data.get("liked_songs", [])
    playlists = data.get("playlists", [])

    print("Syncing liked songs...")
    for track in liked_songs:
        query = f"{track['name']} {track['artists']}"
        vid = _search_track(yt, query, track["duration_ms"])
        if vid:
            try:
                _like_song(yt, vid)
            except Exception:
                failed.append({"playlist": "Liked Songs", **track})
        else:
            failed.append({"playlist": "Liked Songs", **track})

    for pl in playlists:
        title = f"spoti-port-{pl['name']}"
        print(f"Syncing playlist {title}...")
        pid = _create_playlist(yt, title)
        vids = []
        for track in pl.get("tracks", []):
            query = f"{track['name']} {track['artists']}"
            vid = _search_track(yt, query, track["duration_ms"])
            if vid:
                vids.append(vid)
            else:
                failed.append({"playlist": pl['name'], **track})
            if len(vids) >= 50:
                _add_to_playlist(yt, pid, vids)
                vids = []
        if vids:
            _add_to_playlist(yt, pid, vids)

    _append_failed(failed)
    if failed:
        print(f"Logged {len(failed)} unmatched tracks to {FAILED_LOG_FILE}")


if __name__ == "__main__":
    import_library("spotify_library.json")
