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

3. Obtain YouTube credentials by creating an OAuth client in the Google Developer Console and save the file as `client_secret.json` in the project root. When importing, your default browser will open for Google sign in.

4. Import the library into YouTube Music:

```bash
python -m spotiport.import_youtube spotify_library.json
```

The script creates new playlists prefixed with `spoti-port-` and attempts to match each track by searching YouTube and selecting the result with the closest duration.

Any songs that cannot be matched are saved to `failed_tracks.json` so you can review and handle them later.

## Spotify API Limits

Spotify's Web API enforces rate limits. The exact numbers aren't published, but if too many requests are made in a short time the API will return HTTP `429 Too Many Requests` along with a `Retry-After` header indicating when you can try again. The export script fetches data sequentially so it generally stays well below these limits, but very large libraries may require waiting if a rate limit response is encountered.
