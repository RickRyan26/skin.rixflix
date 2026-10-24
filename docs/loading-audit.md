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
