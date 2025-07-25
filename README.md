# spoti-port

## Mission Statement

**spoti-port** exists to empower users with true ownership and portability of their music libraries. Tired of having your favorite songs, playlists, and collections locked within a single streaming service? This project aims to break down those barriers by enabling you to export your liked songs, playlists, and more from Spotify, and seamlessly transfer them to other platforms such as YouTube Music. Additionally, spoti-port aspires to provide tools for automating the download of your music in high-quality formats like MP3 and FLAC.

**Our mission:** Make your music library truly portable—giving you the freedom to enjoy your collection anywhere, on any platform, and in any format you choose.

## Usage

1. Install dependencies:

```bash
pip install -r requirements.txt
```


2. Export your Spotify library. On first run a browser window will open so you can log into Spotify and authorize the app. If Spotify API credentials are not found, you will be prompted to enter them. You can obtain these by registering an application in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard):


```bash
python -m spotiport.export_spotify
```

This creates a `spotify_library.json` file containing your liked songs and playlists.
The credentials you enter will be saved in a local `.env` file for future use.


3. Authenticate with YouTube Music. On the first run the import script will
   prompt you to supply request headers from your logged in YouTube Music
   session. Simply follow the on‑screen instructions and paste the headers when
   asked. The configuration is stored locally in `headers_auth.json` so you only
   need to do this once. No Google Cloud project or OAuth credentials are
   required.

   Be sure to copy the raw HTTP request headers from an authenticated request
   to `music.youtube.com` (for example a `/browse` request) via your browser's
   developer tools. The file should include values like `cookie`,
   `x-goog-authuser` and an `Authorization` header containing `SAPISIDHASH`.
   Supplying OAuth JSON or other data will cause errors such as
   `oauth JSON provided via auth argument` when the import script starts.


4. Import the library into YouTube Music. The command now asks which parts of
   your library you want to sync—**Liked Songs**, specific playlists, or
   everything:

```bash
python -m spotiport.import_youtube spotify_library.json
```

The script creates new playlists prefixed with `spoti-port-` and attempts to
match each track by searching YouTube and selecting the result with the closest
duration. After each item completes you're asked if you want to sync another.
Any songs that cannot be matched are appended to `failed_tracks.json` so you can
review them later.

### Browser-based import

If you prefer not to create a Google Cloud project you can use the alternative
browser-driven script. It launches a temporary browser window so you can log in
to YouTube Music and automatically captures the required authentication headers.
Subsequent synchronization runs completely headless:

```bash
python -m spotiport.import_youtube_browser spotify_library.json
```

This method uses the unofficial YouTube Music API and Playwright to automate
requests. Make sure automated access complies with YouTube's Terms of Service.

## Spotify API Limits

Spotify's Web API enforces rate limits. The exact numbers aren't published, but if too many requests are made in a short time the API will return HTTP `429 Too Many Requests` along with a `Retry-After` header indicating when you can try again. The export script fetches data sequentially so it generally stays well below these limits, but very large libraries may require waiting if a rate limit response is encountered.

## YouTube API Limits

YouTube Data API v3 enforces a daily quota system based on "units." By default, each Google Cloud project is granted **10,000 units per day**. Different API requests consume different amounts of units—for example, a search query costs 100 units, while fetching playlist or video details typically costs 1 unit per request. If your application exceeds the daily quota, the API will return a `403 quotaExceeded` error and you will need to wait until the quota resets at midnight Pacific Time. For most users, typical library import operations stay well within these limits, but very large libraries or frequent operations may require careful management of API usage. You can request a quota increase through the Google Cloud Console if needed.
