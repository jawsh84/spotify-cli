"""Parse functions adapted from spotify-mcp/utils.py — pure functions, no external deps."""

from collections import defaultdict
from typing import Optional, Dict
from urllib.parse import quote, urlparse, urlunparse


def normalize_redirect_uri(url: str) -> str:
    if not url:
        return url
    parsed = urlparse(url)
    if parsed.netloc == "localhost" or parsed.netloc.startswith("localhost:"):
        port = ""
        if ":" in parsed.netloc:
            port = ":" + parsed.netloc.split(":")[1]
        parsed = parsed._replace(netloc=f"127.0.0.1{port}")
    return urlunparse(parsed)


def parse_track(track_item: dict, detailed=False) -> Optional[dict]:
    if not track_item:
        return None
    result = {
        "name": track_item["name"],
        "id": track_item["id"],
    }
    if "is_playing" in track_item:
        result["is_playing"] = track_item["is_playing"]
    if detailed:
        result["album"] = parse_album(track_item.get("album"))
        for k in ["track_number", "duration_ms"]:
            result[k] = track_item.get(k)
    if not track_item.get("is_playable", True):
        result["is_playable"] = False
    artists = [a["name"] for a in track_item["artists"]]
    if detailed:
        artists = [parse_artist(a) for a in track_item["artists"]]
    result["artist"] = artists[0] if len(artists) == 1 else artists
    return result


def parse_artist(artist_item: dict, detailed=False) -> Optional[dict]:
    if not artist_item:
        return None
    result = {"name": artist_item["name"], "id": artist_item["id"]}
    if detailed:
        result["genres"] = artist_item.get("genres")
        result["followers"] = artist_item.get("followers", {}).get("total")
        result["popularity"] = artist_item.get("popularity")
    return result


def parse_album(album_item: dict, detailed=False) -> Optional[dict]:
    if not album_item:
        return None
    result = {"name": album_item["name"], "id": album_item["id"]}
    artists = [a["name"] for a in album_item["artists"]]
    if detailed:
        tracks = []
        for t in album_item.get("tracks", {}).get("items", []):
            tracks.append(parse_track(t))
        result["tracks"] = tracks
        artists = [parse_artist(a) for a in album_item["artists"]]
        for k in ["total_tracks", "release_date", "genres"]:
            result[k] = album_item.get(k)
    result["artist"] = artists[0] if len(artists) == 1 else artists
    return result


def parse_playlist(playlist_item: dict, username=None, detailed=False) -> Optional[dict]:
    if not playlist_item:
        return None
    result = {
        "name": playlist_item["name"],
        "id": playlist_item["id"],
        "owner": playlist_item["owner"]["display_name"],
        "total_tracks": playlist_item["tracks"]["total"],
    }
    if username:
        result["user_is_owner"] = playlist_item["owner"]["display_name"] == username
    if detailed:
        result["description"] = playlist_item.get("description")
        tracks = []
        for t in playlist_item["tracks"]["items"]:
            tracks.append(parse_track(t["track"]))
        result["tracks"] = tracks
    return result


def parse_search_results(results: Dict, qtype: str, username: Optional[str] = None):
    _results = defaultdict(list)
    for q in qtype.split(","):
        match q:
            case "track":
                for item in results["tracks"]["items"]:
                    if item:
                        _results["tracks"].append(parse_track(item))
            case "artist":
                for item in results["artists"]["items"]:
                    if item:
                        _results["artists"].append(parse_artist(item))
            case "playlist":
                for item in results["playlists"]["items"]:
                    if item:
                        _results["playlists"].append(parse_playlist(item, username))
            case "album":
                for item in results["albums"]["items"]:
                    if item:
                        _results["albums"].append(parse_album(item))
    return dict(_results)
