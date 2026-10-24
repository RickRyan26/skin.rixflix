# Loading presentation audit — 1.12.36

Rule: no generic loading sentence; orbit spinner (`Furniture_Busy_Spinner`) where shape is unknown.

- **Search** (`Includes_Search.xml` `Search_Info_Panel`, `Label_Search_*`): "Searching..." and
  "Looking for ... " removed. While providers answer, the title shows the query and the orbit
  spinner shows beneath it. Empty/no-match messages are results, not loading, and stay.
- **Trailer**: `Label_RixFlix_TrailerButton` ("Loading Trailer…") was unused; removed. The
  trailer wait is the Furniture_Busy card (`rixflix_trailer.py` property drives it).
- **Volume** (`DialogVolumeBar.xml`): card hidden since 1.12.33.
- **Home rows** (`View_ComboList_Loading_Item`): already content skeletons.
- **Acceptable remaining**: video buffering percent card (real progress), DialogBusy card
  (Kodi-driven, spinner + short label), diagnostic failures, player seek/progress.

## 1.12.37 — shared orbit asset

`media/dialog/loading-spinner.png` (used by every spinner through `Defs_BusySpinner_Image`) is
now the rix-ui `PanelLoadingOrbit` translated to a texture: faint full ring, tail fading to a
bright head dot with glow (white, tinted by `ColorHighlight`). `media/busy/*` (three grey dots)
is unused by any XML. The rotate animation is clockwise, 1600 ms, sine in-out, matching the web
`panel-orbit-spin`. Kodi has no conic-gradient/mask, so the look is baked into the PNG.

Generic labels removed: `Furniture_Busy[_Main]` defaults (`$LOCALIZE[20186]`, "Loading..."),
`Object_BusySpinner` default label, and the widget busy card's "Loading" (31023) title. Every
live Furniture_Busy caller already passes `haslabel=false` or real data (download progress,
notification text). `31046` "No Results" and `31281` "Welcome" are results/empty states, kept.
