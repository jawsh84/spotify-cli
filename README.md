# sp — Spotify CLI

A minimal Spotify CLI built for use by Claude agents. Wraps [spotipy](https://spotipy.readthedocs.io/) with a clean command interface and optional `--json` output for structured consumption.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A [Spotify Developer](https://developer.spotify.com/dashboard) app

## Setup

### 1. Create a Spotify app

Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), create an app, and add `http://127.0.0.1:8888/callback` as a redirect URI.

### 2. Install

```bash
uv tool install /path/to/spotify-cli
```

### 3. Configure auth

Set three environment variables:

```bash
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
export SPOTIFY_REDIRECT_URI="http://127.0.0.1:8888/callback"
```

On first run, `sp` will open a browser for OAuth authorization. The token is cached locally at `.cache` and auto-refreshes.

## Commands

```
PLAYBACK
  sp now                         Currently playing track
  sp play [uri]                  Resume or play URI
  sp pause                       Pause playback
  sp skip [n]                    Skip track(s)
  sp prev                        Previous track
  sp volume <0-100>              Set volume
  sp devices                     List devices

QUEUE
  sp queue                       Show queue
  sp queue add <uri>             Add to queue

SEARCH
  sp search <query> [--type TYPE] [--limit N]
    TYPE: track (default), album, artist, playlist
    Multiple types: --type track,album

INFO
  sp info <uri>                  Detail on any Spotify item
    URI format: spotify:track:ID, spotify:album:ID, etc.

PLAYLISTS
  sp playlists [--limit N]       List user's playlists
  sp playlist <id>               Show playlist tracks
  sp playlist <id> add <ids>     Add tracks (comma-separated IDs)
  sp playlist <id> remove <ids>  Remove tracks (comma-separated IDs)
  sp playlist create "<name>" [--private] [--desc "..."]

LIBRARY
  sp saved tracks [--limit N]    Liked tracks
  sp saved albums [--limit N]    Saved albums
  sp save track <ids>            Like tracks (comma-separated IDs)
  sp save album <ids>            Save albums (comma-separated IDs)
  sp unsave track <ids>          Unlike tracks
  sp unsave album <ids>          Unsave albums

LISTENING HISTORY
  sp recent [--limit N]          Recently played
  sp top tracks [--range short|medium|long] [--limit N]
  sp top artists [--range short|medium|long] [--limit N]

FLAGS
  --json                         JSON output (all commands)
```

## Examples

```bash
sp now
sp search "bicep" --type artist
sp saved albums --limit 10
sp top tracks --range short
sp playlist 37i9dQZF1DXcBWIGoYBM5M
sp info spotify:album:4LH4d3cOWNNsVw41Gqt2kv
sp queue add spotify:track:3n3Ppam7vgaVa1iaRUc9Lp
```

All commands support `--json` for structured output:

```bash
sp now --json
sp search "floating points" --json
```

## Agent integration

For Claude agent usage, prefix commands with the required env vars:

```bash
SPOTIFY_CLIENT_ID="..." SPOTIFY_CLIENT_SECRET="..." SPOTIFY_REDIRECT_URI="..." sp <command>
```

Use `sp agent` for a detailed command reference with full syntax, return shapes, and usage tips — designed for LLM consumption.
