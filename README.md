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

3. Obtain YouTube credentials by creating an OAuth client in the Google Developer Console and save the file as `client_secret.json` in the project root. When importing, your default browser will open for Google sign in. **Register `http://localhost:8080/` as an authorized redirect URI** so the authentication flow can use a fixed callback URL.

### Enable YouTube Data API v3

Make sure the **YouTube Data API v3** is enabled in the same Google Cloud project where you created the OAuth credentials. If it isn't enabled, the import command will fail with a 403 error indicating that the API is disabled or hasn't been used in your project.

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

## Spotify API Limits

Spotify's Web API enforces rate limits. The exact numbers aren't published, but if too many requests are made in a short time the API will return HTTP `429 Too Many Requests` along with a `Retry-After` header indicating when you can try again. The export script fetches data sequentially so it generally stays well below these limits, but very large libraries may require waiting if a rate limit response is encountered.

## YouTube API Limits

YouTube Data API v3 enforces a daily quota system based on "units." By default, each Google Cloud project is granted **10,000 units per day**. Different API requests consume different amounts of units—for example, a search query costs 100 units, while fetching playlist or video details typically costs 1 unit per request. If your application exceeds the daily quota, the API will return a `403 quotaExceeded` error and you will need to wait until the quota resets at midnight Pacific Time. For most users, typical library import operations stay well within these limits, but very large libraries or frequent operations may require careful management of API usage. You can request a quota increase through the Google Cloud Console if needed.
