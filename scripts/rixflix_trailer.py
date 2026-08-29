"""Resolve a library YouTube trailer to signed HLS for background or on-demand play."""

import json
import os
import re
import subprocess
import sys
import time
from urllib.parse import parse_qs, urlparse

import xbmc
import xbmcgui
import xbmcvfs


REQUEST_PROPERTY = "RixFlix.AutoplayTrailer"
RESOLVED_PROPERTY = "RixFlix.AutoplayTrailerResolved"
UNAVAILABLE_PROPERTY = "RixFlix.UnavailableTrailer"
RESOLVING_PROPERTY = "RixFlix.TrailerResolving"
ON_DEMAND_PROPERTY = "RixFlix.OnDemandTrailerResolved"
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def log(message, level=xbmc.LOGINFO):
    xbmc.log(f"RixFlix trailer: {message}", level)


def clear_if_owned(home, requested):
    if home.getProperty(REQUEST_PROPERTY) == requested:
        home.clearProperty(RESOLVED_PROPERTY)
        home.clearProperty(REQUEST_PROPERTY)


def clear_if_equal(home, name, value):
    if home.getProperty(name) == value:
        home.clearProperty(name)


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
    foreground_claimed = False
    try:
        if mode not in ("background", "foreground"):
            raise ValueError("unsupported playback mode")
        if mode == "foreground":
            if home.getProperty(RESOLVING_PROPERTY):
                log("ignored duplicate on-demand request")
                return
            home.setProperty(RESOLVING_PROPERTY, requested)
            foreground_claimed = True
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
            if home.getProperty(RESOLVING_PROPERTY) != requested:
                log("on-demand request cancelled during resolution")
                return
            if home.getProperty(UNAVAILABLE_PROPERTY) == requested:
                home.clearProperty(UNAVAILABLE_PROPERTY)
            home.setProperty(ON_DEMAND_PROPERTY, manifest)
            player = xbmc.Player()
            player.play(manifest, windowed=False)
            monitor = xbmc.Monitor()
            deadline = time.monotonic() + 20
            started = False
            saw_fullscreen = False
            while not monitor.abortRequested():
                player_path = xbmc.getInfoLabel("Player.Filenameandpath")
                playing = player.isPlayingVideo()
                if not started and home.getProperty(RESOLVING_PROPERTY) != requested:
                    if player_path == manifest:
                        player.stop()
                    log("on-demand request cancelled before playback")
                    break
                if playing and player_path and player_path != manifest:
                    break
                if playing:
                    if not started:
                        started = True
                        clear_if_equal(home, RESOLVING_PROPERTY, requested)
                        log("started on-demand HLS trailer")
                    if xbmc.getCondVisibility("Window.IsActive(fullscreenvideo)"):
                        saw_fullscreen = True
                    elif saw_fullscreen:
                        # Back returned to the movie surface: stop only our exact signed URL.
                        if xbmc.getInfoLabel("Player.Filenameandpath") == manifest:
                            player.stop()
                        break
                elif started:
                    break
                elif time.monotonic() >= deadline:
                    if player_path == manifest:
                        player.stop()
                    home.setProperty(UNAVAILABLE_PROPERTY, requested)
                    log("on-demand player did not start before deadline", xbmc.LOGWARNING)
                    break
                if monitor.waitForAbort(0.2):
                    break
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        if mode == "background":
            clear_if_owned(home, requested)
        elif requested:
            # Hide this button for the rest of the session; the underlying movie UI stays put.
            home.setProperty(UNAVAILABLE_PROPERTY, requested)
        log(f"resolution failed: {type(exc).__name__}: {exc}", xbmc.LOGWARNING)
    finally:
        if foreground_claimed:
            clear_if_equal(home, RESOLVING_PROPERTY, requested)
            clear_if_equal(home, ON_DEMAND_PROPERTY, locals().get("manifest", ""))


if __name__ == "__main__":
    main()
