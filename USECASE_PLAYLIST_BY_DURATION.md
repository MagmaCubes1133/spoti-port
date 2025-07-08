# Use Case: Creating Multiple Playlists by Duration and Adding Songs

This guide demonstrates how to use the Spoti-Port tool to create multiple YouTube playlists from a Spotify export, using **duration as the primary matching metric**. It includes step-by-step instructions, example commands, and suggestions for visual references or screencasts.

---

## Prerequisites
- Python 3.8+
- Required packages from `requirements.txt`
- A valid `client_secret.json` for YouTube API access (OAuth credentials)
- A Spotify library export in JSON format (e.g., `spotify_library.json`)

---

## Step 1: Prepare Your Environment

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Place your `client_secret.json` in the project root.**
3. **Ensure your Spotify export file (e.g., `spotify_library.json`) is present.**

> **Visual Reference:** Screenshot of the project directory with all required files.

---

## Step 2: Run the Import Script

1. **Start the import process:**
   ```bash
   python -m spotiport.import_youtube spotify_library.json
   ```
2. **Authenticate with Google:**
   - A browser window will open for you to log in and authorize YouTube access.

> **Visual Reference:** Screencast of the authentication flow and terminal output.

---

## Step 3: Select Playlists to Sync

- The script will prompt you to select which playlists (or liked songs) to sync.
- You can choose to sync all, or select individual playlists.

> **Visual Reference:** Screenshot of the terminal prompt with playlist options.

---

## Step 4: Playlist Creation and Song Matching

- For each selected playlist:
  1. The script creates a new YouTube playlist (if it doesn't already exist).
  2. For each track, it:
     - Decodes the song name and artist (handles Unicode/HTML).
     - Searches YouTube for videos matching the song name and artist.
     - **Filters results to those within ±10 seconds of the original track duration.**
     - Picks the video whose title is most similar to the song name + artist.
     - Adds the best match to the playlist.

> **Visual Reference:**
> - Screencast showing the script output as it processes each track.
> - Example log output:
>   ```
>   Syncing playlist: My Favorite Songs
>   Added: BTS - Dynamite (Official Video) [3:19]
>   Added: BLACKPINK - How You Like That [3:02]
>   ...
>   ```

---

## Step 5: Review Results

- When finished, the script will log any tracks it could not match (e.g., due to no video within the duration window).
- Playlists will appear in your YouTube account, named with the prefix `spoti-port-`.

> **Visual Reference:**
> - Screenshot of the new playlists in YouTube.
> - Example of the `failed_tracks.json` file for unmatched songs.

---

## Example End Results

- **YouTube Playlist:**
  - Name: `spoti-port-My Favorite Songs`
  - Songs: All matched tracks, each within 10 seconds of the original duration, with best title match.
- **Failed Tracks Log:**
  - File: `failed_tracks.json`
  - Content: List of tracks that could not be matched within the tolerance.

---

## Troubleshooting
- If a playlist or song is missing, check `failed_tracks.json` for details.
- Ensure your YouTube account is authorized and has no API quota issues.

---

## Screencast/Visual Reference Suggestions
- **Step 1:** Directory structure screenshot
- **Step 2:** Authentication screencast
- **Step 3:** Playlist selection prompt screenshot
- **Step 4:** Script processing screencast (showing duration filtering and title matching)
- **Step 5:** YouTube playlist screenshot and failed log example

---

For further customization or debugging, see the code in `spotiport/import_youtube.py`. 