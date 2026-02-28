"""Spotipy wrapper — auth + all API methods."""

import os
from pathlib import Path
from typing import Optional, List

import spotipy
from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

from . import utils

CACHE_PATH = str(Path.home() / ".claude" / "tools" / "spotify-cli" / ".cache")

SCOPES = ",".join([
    "user-library-read",
    "user-library-modify",
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-private",
    "playlist-modify-public",
    "user-top-read",
    "user-read-recently-played",
])


def get_client() -> spotipy.Spotify:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI")
    if not all([client_id, client_secret, redirect_uri]):
        raise SystemExit("Missing SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, or SPOTIFY_REDIRECT_URI")
    redirect_uri = utils.normalize_redirect_uri(redirect_uri)
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPES,
        cache_handler=CacheFileHandler(cache_path=CACHE_PATH),
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def _get_username(sp: spotipy.Spotify) -> str:
    return sp.current_user()["display_name"]


def _get_device_id(sp: spotipy.Spotify) -> Optional[str]:
    """Get active device, or first available."""
    devices = sp.devices().get("devices", [])
    if not devices:
        return None
    for d in devices:
        if d.get("is_active"):
            return d["id"]
    return devices[0]["id"]


# --- Playback ---

def now_playing(sp: spotipy.Spotify) -> Optional[dict]:
    current = sp.current_user_playing_track()
    if not current or current.get("currently_playing_type") != "track":
        return None
    track = utils.parse_track(current["item"])
    track["is_playing"] = current.get("is_playing", False)
    return track


def play(sp: spotipy.Spotify, uri: Optional[str] = None):
    device_id = _get_device_id(sp)
    if not uri:
        sp.start_playback(device_id=device_id)
        return
    if uri.startswith("spotify:track:"):
        sp.start_playback(uris=[uri], device_id=device_id)
    else:
        sp.start_playback(context_uri=uri, device_id=device_id)


def pause(sp: spotipy.Spotify):
    device_id = _get_device_id(sp)
    sp.pause_playback(device_id=device_id)


def skip(sp: spotipy.Spotify, n: int = 1):
    for _ in range(n):
        sp.next_track()


def prev(sp: spotipy.Spotify):
    sp.previous_track()


def volume(sp: spotipy.Spotify, level: int):
    sp.volume(level)


def devices(sp: spotipy.Spotify) -> list:
    return sp.devices().get("devices", [])


# --- Queue ---

def get_queue(sp: spotipy.Spotify) -> dict:
    q = sp.queue()
    return {
        "currently_playing": utils.parse_track(q.get("currently_playing")) if q.get("currently_playing") else None,
        "queue": [utils.parse_track(t) for t in q.get("queue", [])],
    }


def queue_add(sp: spotipy.Spotify, uri: str):
    sp.add_to_queue(uri)


# --- Search ---

def search(sp: spotipy.Spotify, query: str, qtype: str = "track", limit: int = 10) -> dict:
    username = _get_username(sp)
    results = sp.search(q=query, type=qtype, limit=limit)
    return utils.parse_search_results(results, qtype, username)


# --- Info ---

def info(sp: spotipy.Spotify, uri: str) -> dict:
    parts = uri.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid URI: {uri}. Expected format: spotify:type:id")
    _, qtype, item_id = parts
    match qtype:
        case "track":
            return utils.parse_track(sp.track(item_id), detailed=True)
        case "album":
            return utils.parse_album(sp.album(item_id), detailed=True)
        case "artist":
            artist = utils.parse_artist(sp.artist(item_id), detailed=True)
            top = sp.artist_top_tracks(item_id)["tracks"]
            albums = sp.artist_albums(item_id)
            artist["top_tracks"] = [utils.parse_track(t) for t in top]
            artist["albums"] = [utils.parse_album(a) for a in albums["items"]]
            return artist
        case "playlist":
            username = _get_username(sp)
            return utils.parse_playlist(sp.playlist(item_id), username, detailed=True)
    raise ValueError(f"Unknown type: {qtype}")


# --- Playlists ---

def playlists(sp: spotipy.Spotify, limit: int = 50) -> list:
    username = _get_username(sp)
    results = sp.current_user_playlists(limit=limit)
    return [utils.parse_playlist(p, username) for p in results["items"]]


def playlist_tracks(sp: spotipy.Spotify, playlist_id: str, limit: int = 100) -> list:
    results = sp.playlist_items(playlist_id, limit=limit)
    return [utils.parse_track(item["track"]) for item in results["items"] if item.get("track")]


def playlist_add(sp: spotipy.Spotify, playlist_id: str, track_ids: List[str]):
    sp.playlist_add_items(playlist_id, track_ids)


def playlist_remove(sp: spotipy.Spotify, playlist_id: str, track_ids: List[str]):
    sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)


def playlist_create(sp: spotipy.Spotify, name: str, public: bool = True, description: str = "") -> dict:
    user_id = sp.current_user()["id"]
    username = _get_username(sp)
    result = sp.user_playlist_create(user=user_id, name=name, public=public, description=description)
    return utils.parse_playlist(result, username, detailed=True)


# --- Library ---

def saved_tracks(sp: spotipy.Spotify, limit: int = 20) -> list:
    results = sp.current_user_saved_tracks(limit=limit)
    return [utils.parse_track(item["track"]) for item in results["items"] if item.get("track")]


def saved_albums(sp: spotipy.Spotify, limit: int = 20) -> list:
    results = sp.current_user_saved_albums(limit=limit)
    return [utils.parse_album(item["album"]) for item in results["items"] if item.get("album")]


def save_tracks(sp: spotipy.Spotify, ids: List[str]):
    sp.current_user_saved_tracks_add(ids)


def save_albums(sp: spotipy.Spotify, ids: List[str]):
    sp.current_user_saved_albums_add(ids)


def unsave_tracks(sp: spotipy.Spotify, ids: List[str]):
    sp.current_user_saved_tracks_delete(ids)


def unsave_albums(sp: spotipy.Spotify, ids: List[str]):
    sp.current_user_saved_albums_delete(ids)


# --- Listening History ---

def recent(sp: spotipy.Spotify, limit: int = 20) -> list:
    results = sp.current_user_recently_played(limit=limit)
    return [utils.parse_track(item["track"]) for item in results["items"] if item.get("track")]


def top_tracks(sp: spotipy.Spotify, time_range: str = "medium_term", limit: int = 20) -> list:
    results = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    return [utils.parse_track(t) for t in results["items"]]


def top_artists(sp: spotipy.Spotify, time_range: str = "medium_term", limit: int = 20) -> list:
    results = sp.current_user_top_artists(limit=limit, time_range=time_range)
    return [utils.parse_artist(a) for a in results["items"]]
