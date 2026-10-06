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
