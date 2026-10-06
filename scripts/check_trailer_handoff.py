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


def check(case, frames, *, duplicate=False, cancel=False, expected_stops=0):
    with tempfile.TemporaryDirectory() as directory:
        properties = {}
        home = SimpleNamespace(
            getProperty=lambda key: properties.get(key, ""),
            setProperty=lambda key, value: properties.__setitem__(key, value),
            clearProperty=lambda key: properties.pop(key, None),
        )
        state = {"tick": 0, "launched": False, "calls": [], "stops": 0}

        def frame():
            if not state["launched"]:
                return ("movie", True, False)
            path, playing, fullscreen = frames[min(state["tick"], len(frames) - 1)]
            return (state["calls"][0] if path == "playlist" else path, playing, fullscreen)

        def play(path, **kwargs):
            assert kwargs == {"windowed": False}
            payload = Path(path).read_text()
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
            with patch.object(module.os.path, "isfile", return_value=True), \
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
