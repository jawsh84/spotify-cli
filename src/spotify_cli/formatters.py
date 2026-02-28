"""Plain text and JSON output formatters."""

import json
from typing import Optional


def _artist_str(item: dict) -> str:
    a = item.get("artist")
    if a is None:
        return "Unknown"
    if isinstance(a, list):
        return ", ".join(n["name"] if isinstance(n, dict) else n for n in a)
    if isinstance(a, dict):
        return a["name"]
    return str(a)


def _ms_to_duration(ms: Optional[int]) -> str:
    if not ms:
        return ""
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


def format_track(t: dict) -> str:
    parts = [f"{t['name']} -- {_artist_str(t)}"]
    if t.get("duration_ms"):
        parts.append(f"[{_ms_to_duration(t['duration_ms'])}]")
    parts.append(f"(ID: {t['id']})")
    return " ".join(parts)


def format_now_playing(t: Optional[dict]) -> str:
    if not t:
        return "Nothing playing."
    status = "Playing" if t.get("is_playing") else "Paused"
    return f"{status}: {t['name']} -- {_artist_str(t)} (ID: {t['id']})"


def format_track_list(tracks: list, numbered: bool = True) -> str:
    if not tracks:
        return "No tracks."
    lines = []
    for i, t in enumerate(tracks, 1):
        line = format_track(t)
        if numbered:
            line = f"{i:>3}. {line}"
        lines.append(line)
    return "\n".join(lines)


def format_artist(a: dict) -> str:
    parts = [a["name"]]
    if a.get("genres"):
        parts.append(f"[{', '.join(a['genres'])}]")
    if a.get("followers") is not None:
        parts.append(f"({a['followers']:,} followers)")
    parts.append(f"(ID: {a['id']})")
    return " ".join(parts)


def format_album(a: dict) -> str:
    parts = [f"{a['name']} -- {_artist_str(a)}"]
    if a.get("release_date"):
        parts.append(f"[{a['release_date']}]")
    if a.get("total_tracks"):
        parts.append(f"({a['total_tracks']} tracks)")
    parts.append(f"(ID: {a['id']})")
    return " ".join(parts)


def format_playlist(p: dict) -> str:
    parts = [f"{p['name']} -- {p.get('owner', '?')}"]
    parts.append(f"({p['total_tracks']} tracks)")
    parts.append(f"(ID: {p['id']})")
    return " ".join(parts)


def format_device(d: dict) -> str:
    active = "*" if d.get("is_active") else " "
    return f"  {active} {d['name']} ({d['type']}) vol:{d.get('volume_percent', '?')}%"


def format_search_results(results: dict) -> str:
    lines = []
    for category, items in results.items():
        lines.append(f"--- {category.upper()} ---")
        for i, item in enumerate(items, 1):
            match category:
                case "tracks":
                    lines.append(f"  {i}. {format_track(item)}")
                case "artists":
                    lines.append(f"  {i}. {format_artist(item)}")
                case "albums":
                    lines.append(f"  {i}. {format_album(item)}")
                case "playlists":
                    lines.append(f"  {i}. {format_playlist(item)}")
        lines.append("")
    return "\n".join(lines).rstrip()


def format_queue(q: dict) -> str:
    lines = []
    cp = q.get("currently_playing")
    if cp:
        lines.append(f"Now: {format_track(cp)}")
    else:
        lines.append("Now: Nothing playing")
    lines.append("")
    queue = q.get("queue", [])
    if not queue:
        lines.append("Queue is empty.")
    else:
        lines.append("Queue:")
        for i, t in enumerate(queue, 1):
            lines.append(f"  {i}. {format_track(t)}")
    return "\n".join(lines)


def format_artist_info(a: dict) -> str:
    lines = [format_artist(a)]
    if a.get("top_tracks"):
        lines.append("\nTop Tracks:")
        for i, t in enumerate(a["top_tracks"], 1):
            lines.append(f"  {i}. {format_track(t)}")
    if a.get("albums"):
        lines.append("\nAlbums:")
        for i, alb in enumerate(a["albums"], 1):
            lines.append(f"  {i}. {format_album(alb)}")
    return "\n".join(lines)


def format_playlist_detail(p: dict) -> str:
    lines = [format_playlist(p)]
    if p.get("description"):
        lines.append(f"  {p['description']}")
    if p.get("tracks"):
        lines.append("")
        for i, t in enumerate(p["tracks"], 1):
            lines.append(f"  {i}. {format_track(t)}")
    return "\n".join(lines)


def as_json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
