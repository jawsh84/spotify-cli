"""sp — Spotify CLI for Claude agent."""

import argparse
import sys

from . import client, formatters


HELP_TEXT = """\
sp — Spotify CLI

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

EXAMPLES
  sp now
  sp search "bicep" --type artist
  sp saved albums --limit 10
  sp top tracks --range short
  sp playlist 37i9dQZF1DXcBWIGoYBM5M
  sp info spotify:album:4LH4d3cOWNNsVw41Gqt2kv
"""

TIME_RANGE_MAP = {"short": "short_term", "medium": "medium_term", "long": "long_term"}


def _parse_ids(s: str) -> list:
    return [x.strip() for x in s.split(",") if x.strip()]


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h", "agent"):
        print(HELP_TEXT)
        return

    use_json = "--json" in args
    if use_json:
        args.remove("--json")

    cmd = args[0]

    try:
        sp = client.get_client()
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    try:
        _dispatch(sp, cmd, args[1:], use_json)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _get_flag(args: list, flag: str, default=None):
    """Extract --flag value from args list, mutating args."""
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            val = args[idx + 1]
            args.pop(idx)  # remove flag
            args.pop(idx)  # remove value
            return val
        args.pop(idx)
    return default


def _dispatch(sp, cmd: str, args: list, use_json: bool):
    match cmd:
        # --- Playback ---
        case "now":
            result = client.now_playing(sp)
            if use_json:
                print(formatters.as_json(result))
            else:
                print(formatters.format_now_playing(result))

        case "play":
            uri = args[0] if args else None
            client.play(sp, uri)
            print("Playing." if uri else "Resumed.")

        case "pause":
            client.pause(sp)
            print("Paused.")

        case "skip":
            n = int(args[0]) if args else 1
            client.skip(sp, n)
            print(f"Skipped {n} track(s).")

        case "prev":
            client.prev(sp)
            print("Previous track.")

        case "volume":
            if not args:
                print("Usage: sp volume <0-100>", file=sys.stderr)
                sys.exit(1)
            level = int(args[0])
            client.volume(sp, level)
            print(f"Volume: {level}%")

        case "devices":
            result = client.devices(sp)
            if use_json:
                print(formatters.as_json(result))
            else:
                if not result:
                    print("No devices found.")
                else:
                    for d in result:
                        print(formatters.format_device(d))

        # --- Queue ---
        case "queue":
            if args and args[0] == "add":
                if len(args) < 2:
                    print("Usage: sp queue add <uri>", file=sys.stderr)
                    sys.exit(1)
                client.queue_add(sp, args[1])
                print("Added to queue.")
            else:
                result = client.get_queue(sp)
                if use_json:
                    print(formatters.as_json(result))
                else:
                    print(formatters.format_queue(result))

        # --- Search ---
        case "search":
            if not args:
                print("Usage: sp search <query> [--type TYPE] [--limit N]", file=sys.stderr)
                sys.exit(1)
            qtype = _get_flag(args, "--type", "track")
            limit = int(_get_flag(args, "--limit", "10"))
            query = " ".join(args)
            result = client.search(sp, query, qtype, limit)
            if use_json:
                print(formatters.as_json(result))
            else:
                print(formatters.format_search_results(result))

        # --- Info ---
        case "info":
            if not args:
                print("Usage: sp info <spotify:type:id>", file=sys.stderr)
                sys.exit(1)
            result = client.info(sp, args[0])
            if use_json:
                print(formatters.as_json(result))
            else:
                # Format based on URI type
                uri_type = args[0].split(":")[1] if ":" in args[0] else ""
                match uri_type:
                    case "artist":
                        print(formatters.format_artist_info(result))
                    case "playlist":
                        print(formatters.format_playlist_detail(result))
                    case "album":
                        lines = [formatters.format_album(result)]
                        if result.get("tracks"):
                            for i, t in enumerate(result["tracks"], 1):
                                lines.append(f"  {i}. {formatters.format_track(t)}")
                        print("\n".join(lines))
                    case _:
                        print(formatters.format_track(result))

        # --- Playlists ---
        case "playlists":
            limit = int(_get_flag(args, "--limit", "50"))
            result = client.playlists(sp, limit)
            if use_json:
                print(formatters.as_json(result))
            else:
                for i, p in enumerate(result, 1):
                    print(f"{i:>3}. {formatters.format_playlist(p)}")

        case "playlist":
            if not args:
                print("Usage: sp playlist <id> [add|remove <ids>]", file=sys.stderr)
                sys.exit(1)
            pid = args[0]
            if len(args) >= 2 and args[1] == "create":
                # Redirect: they typed "sp playlist create ..."
                _dispatch(sp, "playlist", ["create"] + args[2:], use_json)
                return
            if len(args) >= 3 and args[1] == "add":
                ids = _parse_ids(args[2])
                client.playlist_add(sp, pid, ids)
                print(f"Added {len(ids)} track(s).")
            elif len(args) >= 3 and args[1] == "remove":
                ids = _parse_ids(args[2])
                client.playlist_remove(sp, pid, ids)
                print(f"Removed {len(ids)} track(s).")
            elif pid == "create":
                # sp playlist create "name" [--private] [--desc "..."]
                if len(args) < 2:
                    print('Usage: sp playlist create "<name>" [--private] [--desc "..."]', file=sys.stderr)
                    sys.exit(1)
                sub_args = list(args[1:])
                is_private = False
                if "--private" in sub_args:
                    is_private = True
                    sub_args.remove("--private")
                desc = _get_flag(sub_args, "--desc", "")
                name = " ".join(sub_args)
                result = client.playlist_create(sp, name, public=not is_private, description=desc)
                if use_json:
                    print(formatters.as_json(result))
                else:
                    print(f"Created: {formatters.format_playlist(result)}")
            else:
                result = client.playlist_tracks(sp, pid)
                if use_json:
                    print(formatters.as_json(result))
                else:
                    print(formatters.format_track_list(result))

        # --- Library ---
        case "saved":
            if not args:
                print("Usage: sp saved tracks|albums [--limit N]", file=sys.stderr)
                sys.exit(1)
            sub = args[0]
            sub_args = list(args[1:])
            limit = int(_get_flag(sub_args, "--limit", "20"))
            match sub:
                case "tracks":
                    result = client.saved_tracks(sp, limit)
                    if use_json:
                        print(formatters.as_json(result))
                    else:
                        print(formatters.format_track_list(result))
                case "albums":
                    result = client.saved_albums(sp, limit)
                    if use_json:
                        print(formatters.as_json(result))
                    else:
                        for i, a in enumerate(result, 1):
                            print(f"{i:>3}. {formatters.format_album(a)}")
                case _:
                    print(f"Unknown: sp saved {sub}. Use 'tracks' or 'albums'.", file=sys.stderr)
                    sys.exit(1)

        case "save":
            if len(args) < 2:
                print("Usage: sp save track|album <ids>", file=sys.stderr)
                sys.exit(1)
            sub = args[0]
            ids = _parse_ids(args[1])
            match sub:
                case "track":
                    client.save_tracks(sp, ids)
                    print(f"Saved {len(ids)} track(s).")
                case "album":
                    client.save_albums(sp, ids)
                    print(f"Saved {len(ids)} album(s).")
                case _:
                    print(f"Unknown: sp save {sub}. Use 'track' or 'album'.", file=sys.stderr)
                    sys.exit(1)

        case "unsave":
            if len(args) < 2:
                print("Usage: sp unsave track|album <ids>", file=sys.stderr)
                sys.exit(1)
            sub = args[0]
            ids = _parse_ids(args[1])
            match sub:
                case "track":
                    client.unsave_tracks(sp, ids)
                    print(f"Removed {len(ids)} track(s).")
                case "album":
                    client.unsave_albums(sp, ids)
                    print(f"Removed {len(ids)} album(s).")
                case _:
                    print(f"Unknown: sp unsave {sub}. Use 'track' or 'album'.", file=sys.stderr)
                    sys.exit(1)

        # --- Listening History ---
        case "recent":
            sub_args = list(args)
            limit = int(_get_flag(sub_args, "--limit", "20"))
            result = client.recent(sp, limit)
            if use_json:
                print(formatters.as_json(result))
            else:
                print(formatters.format_track_list(result))

        case "top":
            if not args:
                print("Usage: sp top tracks|artists [--range short|medium|long] [--limit N]", file=sys.stderr)
                sys.exit(1)
            sub = args[0]
            sub_args = list(args[1:])
            time_range = _get_flag(sub_args, "--range", "medium")
            limit = int(_get_flag(sub_args, "--limit", "20"))
            time_range_val = TIME_RANGE_MAP.get(time_range, "medium_term")
            match sub:
                case "tracks":
                    result = client.top_tracks(sp, time_range_val, limit)
                    if use_json:
                        print(formatters.as_json(result))
                    else:
                        print(formatters.format_track_list(result))
                case "artists":
                    result = client.top_artists(sp, time_range_val, limit)
                    if use_json:
                        print(formatters.as_json(result))
                    else:
                        for i, a in enumerate(result, 1):
                            print(f"{i:>3}. {formatters.format_artist(a)}")
                case _:
                    print(f"Unknown: sp top {sub}. Use 'tracks' or 'artists'.", file=sys.stderr)
                    sys.exit(1)

        case _:
            print(f"Unknown command: {cmd}. Run 'sp help' for usage.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
