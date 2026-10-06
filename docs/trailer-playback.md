# Foreground trailer handoff — 1.10.2

Keep InputStream Adaptive for YouTube's separate HLS audio/video variants. Native
demux stalled on the AM9. Launch a temporary UTF-8 M3U8 containing `#KODIPROP`
inputstream, HLS manifest type and MIME metadata via `Player.play(path,
windowed=False)`, with no ListItem argument. Retain the file until the ownership
monitor exits, then remove it; never mutate a shared Python video playlist.

Kodi 22 source (20260823 snapshot) explains the crash: legacy `Player.cpp:108`
posts `TMSG_MEDIA_PLAY` with param2=0 for `play(URL, ListItem)`. In
`PlayListPlayer.cpp:976` that branch indexes the current playlist without checking
the current-song bounds. The no-ListItem overload posts (-1, -1), which enters
the list branch, clears/adds its playlist and calls bounded `Play(int)`.
`CPlayList::Expand` loads the local M3U before opening its media entry.
`PlayListM3U.cpp` copies KODIPROP values to the resulting item and turns the
`mimetype` property into a MIME type with content lookup disabled.

One nonblocking Linux file lock owns the entire foreground script, from resolution
through playback. Do not unlink the lock file: competing processes must lock the
same inode. Window properties still drive the loading label and cancellation, but
cannot serve as an atomic mutex. After posting play, the previous movie can remain
visible to Kodi's player queries. Keep ownership until the exact signed manifest
is playing, the start deadline expires, cancellation arrives, or a different new
URL replaces playback. Duplicate requests are rejected even after loading ends.
Kodi retains the unique playlist filename as the item path and the manifest as
its dynamic path; accept either exact value as owned. Back stops only that owned
item after fullscreen has been observed.

`python3 scripts/check_trailer_handoff.py` exercises the handoff with fake Kodi
queries and real file locks. It proves Python behavior and the playlist payload;
it does not prove live decoder or HDMI behavior. Box activation and live playback
verification belong to the parent recovery session, once the player is idle.

## Live theater verification — 2026-10-06 PDT

On Rick's idle-box request, `am9-deploy status` confirmed the installed
`eb96f7f3` source pin, skin 1.10.2 and installed-source verification PASS. Kodi's
authenticated local JSON-RPC API was reachable from this session. The host broker
remains the route for SSH/logs; no broker widening, redeploy or restart was needed.

The Home spotlight's actual Play Trailer button for I Am Legend was selected twice
at 00:15:42. The fresh log recorded duplicate rejection at 00:15:43.273, one private
M3U8 open at 00:15:51.712, ISA manifest parsing at 00:15:52.148 and owned startup at
00:15:52.955. Player queries confirmed fullscreen 1920×1080 VP9 video, two-channel
AAC audio, speed 1 and advancing playback. The audio log confirmed a 44.1 kHz
two-channel output stream. Back returned Home, stopped playback and cleared both
resolving and ownership properties. No separate emergency Stop was required.

Back during a second resolution cleared the loading property. The log confirmed
`on-demand request cancelled during resolution` at 00:16:49.652; polling for 18
seconds observed no late playback. Back also followed the Home surface's ordinary
navigation; the harness restored Home/action focus before the next playback.

A second title, Little Brother, opened its private M3U8 at 00:17:48.024 and logged
owned startup at 00:17:48.726. The final sample at 62.19 seconds after Select showed
52 seconds of advancing playback, speed 1, VP9, AAC and fullscreen. This crossed
the original roughly 41-second crash window. Back again stopped the trailer;
JSONRPC.Ping returned pong, Home was active and the broker reported idle. Fresh
logs contained no playlist out-of-range error, audio stall or crash in these runs.

Sanitized runtime measurements are in
`/home/rick/tmpbuild/trailer-live-20261006.json` and
`/home/rick/tmpbuild/trailer-sustained-20261006.json`. These API/log measurements prove
decoder activity and ownership behavior, not a listener's subjective audio result
or a physical TV input switch.
