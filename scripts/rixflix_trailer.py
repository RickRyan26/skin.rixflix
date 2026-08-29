"""Resolve a library YouTube trailer to signed HLS for background or on-demand play."""

import json
import os
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlparse

import xbmc
import xbmcgui
import xbmcvfs


REQUEST_PROPERTY = "RixFlix.AutoplayTrailer"
RESOLVED_PROPERTY = "RixFlix.AutoplayTrailerResolved"
UNAVAILABLE_PROPERTY = "RixFlix.UnavailableTrailer"
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def log(message, level=xbmc.LOGINFO):
    xbmc.log(f"RixFlix trailer: {message}", level)


def clear_if_owned(home, requested):
    if home.getProperty(REQUEST_PROPERTY) == requested:
        home.clearProperty(RESOLVED_PROPERTY)
        home.clearProperty(REQUEST_PROPERTY)


def youtube_watch_url(plugin_url):
    parsed = urlparse(plugin_url)
    video_id = (parse_qs(parsed.query).get("video_id") or [""])[0]
    if (
        parsed.scheme != "plugin"
        or parsed.netloc != "plugin.video.youtube"
        or parsed.path.rstrip("/") != "/play"
        or not VIDEO_ID.fullmatch(video_id)
    ):
        raise ValueError("unsupported trailer URL")
    return f"https://www.youtube.com/watch?v={video_id}"


def hls_manifest(document):
    candidates = {
        item.get("manifest_url", "")
        for item in document.get("formats", [])
        if item.get("protocol") == "m3u8_native"
    }
    candidates.discard("")
    if len(candidates) != 1:
        raise ValueError("YouTube did not expose one HLS master manifest")
    manifest = candidates.pop()
    parsed = urlparse(manifest)
    if parsed.scheme != "https" or parsed.hostname != "manifest.googlevideo.com":
        raise ValueError("refusing an unexpected HLS manifest host")
    return manifest


def main():
    requested = sys.argv[1] if len(sys.argv) >= 2 else ""
    mode = sys.argv[2] if len(sys.argv) == 3 else "background"
    home = xbmcgui.Window(10000)
    try:
        if mode not in ("background", "foreground"):
            raise ValueError("unsupported playback mode")
        watch_url = youtube_watch_url(requested)
        resolver = xbmcvfs.translatePath("special://skin/resources/bin/yt-dlp")
        if not os.path.isfile(resolver):
            raise FileNotFoundError("pinned yt-dlp resolver is missing")
        result = subprocess.run(
            [resolver, "--no-warnings", "--no-playlist", "--dump-single-json", watch_url],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        manifest = hls_manifest(json.loads(result.stdout))
        if mode == "background":
            if home.getProperty(REQUEST_PROPERTY) != requested:
                log("selection changed during resolution; discarded stale result")
                return
            home.setProperty(RESOLVED_PROPERTY, manifest)
            xbmc.Player().play(manifest, windowed=True)
            log("started owned background HLS trailer")
        else:
            if home.getProperty(UNAVAILABLE_PROPERTY) == requested:
                home.clearProperty(UNAVAILABLE_PROPERTY)
            xbmc.Player().play(manifest, windowed=False)
            log("started on-demand HLS trailer")
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        if mode == "background":
            clear_if_owned(home, requested)
        elif requested:
            # Hide this button for the rest of the session; the underlying movie UI stays put.
            home.setProperty(UNAVAILABLE_PROPERTY, requested)
        log(f"resolution failed: {type(exc).__name__}: {exc}", xbmc.LOGWARNING)


if __name__ == "__main__":
    main()
