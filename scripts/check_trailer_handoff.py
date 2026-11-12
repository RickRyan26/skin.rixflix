"""Focused reproduction of the asynchronous trailer ownership/crash regression."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True


REQUEST = "plugin://plugin.video.youtube/play/?video_id=abcdefghijk"
MANIFEST = "https://manifest.googlevideo.com/api/manifest/hls_variant/test"


def cache(root, *, row=False, size=None):
    """A box cache holding REQUEST's trailer, as rixflix-trailer-cache.py publishes it."""
    key = "movie-7" if row else "yt-abcdefghijk"
    folder = Path(root) if row else Path(root, "extra")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (key + ".mp4")
    path.write_bytes(b"whole muxed trailer")
    entry = {"file": str(path), "bytes": path.stat().st_size if size is None else size, "trailer": REQUEST}
    ledger = {"entries": {key: entry}}
    if row:
        ledger["set"] = {key: {}}
    (folder / "index.json").write_text(json.dumps(ledger))
    return key, str(path)


def check(case, frames, *, duplicate=False, cancel=False, expected_stops=0, cached=None, preview=False):
    with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as root:
        properties = {}
        home = SimpleNamespace(
            getProperty=lambda key: properties.get(key, ""),
            setProperty=lambda key, value: properties.__setitem__(key, value),
            clearProperty=lambda key: properties.pop(key, None),
        )
        state = {"tick": 0, "launched": False, "calls": [], "stops": 0}
        local = None
        if cached == "extra":
            local = cache(root)
        elif cached == "row":
            local = cache(root, row=True)
        elif cached == "truncated":
            cache(root, size=5)  # ledger and file disagree: not a whole file, resolve instead

        def frame():
            if not state["launched"]:
                return ("movie", True, False)
            path, playing, fullscreen = frames[min(state["tick"], len(frames) - 1)]
            path = {"playlist": state["calls"][0], "file": local[1] if local else ""}.get(path, path)
            return (path, playing, fullscreen)

        def play(path, **kwargs):
            assert kwargs == {"windowed": False}
            payload = Path(path).read_text()
            if local:
                # A cached file: the resident's exact private playlist, no inputstream.
                assert payload == "#EXTM3U\n#EXTINF:-1,Trailer\n" + local[1] + "\n"
                assert Path(path).name == "local-%s.m3u8" % local[0].replace("-", "_")
            else:
                assert payload.endswith(MANIFEST + "\n")
                for prop in ("inputstream=inputstream.adaptive",
                             "inputstream.adaptive.manifest_type=hls",
                             "mimetype=application/vnd.apple.mpegurl"):
                    assert "#KODIPROP:" + prop + "\n" in payload
            state["calls"].append(path)
            state["launched"] = True

        def wait(_):
            if duplicate:
                # Try both while the old movie is reported and after loading clears.
                module.main()
                assert len(state["calls"]) == 1
            state["tick"] += 1
            assert state["tick"] < 30, "monitor did not terminate"
            return False

        def resolve(*args, **kwargs):
            assert not local, "a cached trailer must never reach the resolver"
            if cancel:
                home.clearProperty(module.RESOLVING_PROPERTY)
            return SimpleNamespace(stdout=json.dumps({"formats": [{
                "protocol": "m3u8_native", "manifest_url": MANIFEST,
            }]}))

        player = SimpleNamespace(
            play=play, isPlayingVideo=lambda: frame()[1],
            stop=lambda: state.__setitem__("stops", state["stops"] + 1),
        )
        xbmc = SimpleNamespace(
            LOGINFO=1, LOGWARNING=2, log=lambda *args: None, Player=lambda: player,
            Monitor=lambda: SimpleNamespace(abortRequested=lambda: False, waitForAbort=wait),
            getInfoLabel=lambda _: frame()[0], getCondVisibility=lambda _: frame()[2],
        )
        spec = importlib.util.spec_from_file_location(
            "trailer_under_check", Path(__file__).with_name("rixflix_trailer.py"))
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            "xbmc": xbmc, "xbmcgui": SimpleNamespace(Window=lambda _: home),
            "xbmcvfs": SimpleNamespace(translatePath=lambda _: directory),
        }), patch.object(sys, "argv", ["trailer", REQUEST, "foreground"]):
            spec.loader.exec_module(module)
            module.CACHE_ROOT = root
            if preview:
                # The resident's hover preview of this same card owns the lock and the player.
                import fcntl
                held = open(Path(directory) / "foreground.lock", "a")
                fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                properties.update({module.PREVIEW_ACTIVE_PROPERTY: "yt-abcdefghijk",
                                   module.PREVIEW_TRAILER_PROPERTY: REQUEST})
                module.main()
                assert properties[module.PREVIEW_PROMOTE_PROPERTY] == "yt-abcdefghijk"
                assert not state["calls"] and not properties.get(module.RESOLVING_PROPERTY)
                # 1.14.8: the key alone promotes, even when the skin-timer hover lags.
                properties[module.PREVIEW_TRAILER_PROPERTY] = "another card"
                del properties[module.PREVIEW_PROMOTE_PROPERTY]
                module.main()
                assert properties[module.PREVIEW_PROMOTE_PROPERTY] == "yt-abcdefghijk"
                # Another card's preview (neither hover nor key match) is not promoted.
                properties[module.PREVIEW_ACTIVE_PROPERTY] = "yt-zzzzzzzzzzz"
                del properties[module.PREVIEW_PROMOTE_PROPERTY]
                module.main()
                assert module.PREVIEW_PROMOTE_PROPERTY not in properties
                held.close()
                print("PASS", case)
                return
            real_isfile = module.os.path.isfile
            with patch.object(module.os.path, "isfile",
                              side_effect=lambda path: True if path == directory else real_isfile(path)), \
                    patch.object(module.subprocess, "run", side_effect=resolve), \
                    patch.object(module.time, "monotonic", side_effect=lambda: state["tick"]):
                module.main()
            assert len(state["calls"]) == (0 if cancel else 1)
            assert state["stops"] == expected_stops
            assert not home.getProperty(module.RESOLVING_PROPERTY)
            assert not home.getProperty(module.ON_DEMAND_PROPERTY)
            assert not list(Path(directory).glob("*.m3u8"))
            if case == "timeout":
                assert home.getProperty(module.UNAVAILABLE_PROPERTY) == REQUEST
            # Lock survives as an inode but its ownership is released.
            import fcntl
            with open(Path(directory) / "foreground.lock", "a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print("PASS", case)


if __name__ == "__main__":
    check("old movie handoff + duplicate Select + Back", [
        ("movie", True, False), ("movie", True, False),
        ("playlist", True, True), ("playlist", True, False),
    ], duplicate=True, expected_stops=1)
    check("manifest path + natural end", [
        (MANIFEST, True, True), ("", False, False),
    ])
    check("replacement movie never stopped", [
        ("playlist", True, True), ("new-movie", True, True),
    ])
    check("replacement during handoff", [("new-movie", True, True)])
    check("timeout", [("movie", True, False)])
    check("cancel during resolution", [], cancel=True)
    check("cached extra-tier trailer + Back", [
        ("playlist", True, True), ("playlist", True, False),
    ], cached="extra", expected_stops=1)
    check("cached Home-row trailer by expanded path + Back", [
        ("file", True, True), ("file", True, False),
    ], cached="row", expected_stops=1)
    check("truncated cache falls back to the resolver", [
        ("playlist", True, True), ("", False, False),
    ], cached="truncated")
    check("OK on a previewing card promotes it", [], preview=True)
