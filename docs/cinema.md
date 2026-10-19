# Cinema presentation — 1.10.0

The Home actions are full 80px surfaces with consistent crimson focus, warm white
type and opaque charcoal secondary actions. Play retains a white resting surface.
All three buttons are direct children of the action grouplist, so the whole visible
surface is clickable and navigation does not depend on a nested Play focus group.
Information now supplies its own id to the shared Info/Back restoration include.

The shared browse header carries the packaged RIXFLIX wordmark and preserves its
location label, with the clock at secondary weight. Section headings use the next
existing type size. Synopsis text is brighter; titles without clearlogo artwork have
a shadow. Dialog surfaces have a slight charcoal lift above the black canvas.
Search and Home controls share the cinema surfaces. Empty searches explain the
commit-on-Done flow, and no-match results give a recovery action.

No new artwork fetch, provider, timer, Python service, or per-item animation is
introduced. Poster geometry, widget limits, series routes and trailer ownership
continue through their existing implementations.

`python3 scripts/validate_cinema.py` checks direct action ownership, focus restoration,
compact layout bounds and all six text/surface contrast pairs (minimum 6.05:1).
The pinned Rixflix installer runs this check before activation and on installed-source
verification, alongside its existing source invariants. This is source validation;
the AM9 live smokes and a Kodi capture remain required for runtime/visual claims.

Contracts: [Kodi buttons](https://kodi.wiki/view/Button_control),
[Kodi labels](https://kodi.wiki/view/Label_control), and
[W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

# Home: more poster, less chrome — 1.12.0

Rick, 2026-10-18: New Releases are just larger posters, cards and rows sit closer,
row titles live inside the row, the spotlight is only Play, Categories lose the red,
and the rows get out of the way of a playing New Releases preview.

**Rows.** Home rows (`widgets_row.xmltemplate`, `widgets_grouplist_home.xmltemplate`)
use the `home_*` constants in `Includes_Constants.xml`. Kodi's grouplist gives each
child a pitch of `top + height` and scrolls a focused child to the viewport top when
`viewport = list top + list height` (`GUIControlGroupList.cpp`, `GUI_MSG_FOCUSED`).
With the 1150px viewport and label top −754, rows are **396px apart** (was 570): the
focused row starts at y500 and ~45% of the next row shows. The first row is aligned
by the 754px bumper. New Releases is always first, and Kodi scrolls the first focusable
row to 0, so its taller posters are paid for by its own list height
(`home_premiere_row_h`, +93px), not by the next row's label. Moving New Releases off
the top would misalign it by that 93px.

**Cards.** Poster rows use `List_Home_Poster_Row`: the standard 260×371 poster, 16px
apart instead of 40 (6.7 across instead of 6.1). New Releases (`Layout_Premiere`) is
the standard poster layout at 325×464, with no ribbon, title, date or badges.
Categories (`Layout_Category`) are plain 300×180 tiles on the poster surface, with
the same thin focus box. The shared `widget_include` mapping still sends search rows
to `List_Poster_Row`; Home has its own `widget_home_include`.

**Titles.** `Widget_Inline_Title` is a −90° label reading top to bottom from the
row's card top, with its line centred on x=40 in the 80px left margin. No header line
is reserved above a row. Kodi clips a label's **pre-rotation** rect to the grouplist
(x ≥ 0). 1.12.0 centred a 371px rect on x=40, and the theater capture read
"v Releases" / "inue Movies". 1.12.1 therefore left-aligns and y-centres the label,
so it rotates about (left, top + 20) (`CGUILabel::Render`), and its rect starts at
the anchor and runs right.

The margin must also stay clear of cards. The row lists used to start at x=0 with
cards offset 80. A row scrolled past its first item therefore drew the previous card
over x=0–64, and in 1.12.1 that card hid "Recently Added". Since 1.12.2 the three
Home lists start at `home_row_list_l` (64) with a 16px item offset. Cards stay at
x=80, and the previous card ends exactly at the list's clip edge.

**Rows above focus.** The grouplist clip starts 16px above the focused cards. The
previous row's progress/count badges hang about 25px below its cards, so their rims
showed as arcs over the focused row (1.12.2 capture, Continue Shows). Since 1.12.3
`widgets_row.xmltemplate` fades any row whose id is lower than the focused control's
while focus is inside grouplist 602 (row ids are 501 + index). The fade takes 200ms,
in step with the scroll, and Up fades the row back in.

**Info panel.** On Home the focused row's panel shows the title and one detail line
(quality, stars, date, runtime). Shows and seasons have no stream details. AF3 gave
them a bare "i" pill, and since 1.12.3 they get "TV". The first pill cannot simply be
dropped, because every later item draws its own leading divider. The plot and the "Ends at" metadata block show only
off Home. Rows below
the focused one are no longer dimmed. All rows dim to 30% only behind the spotlight.

**Spotlight.** It has only Play (311): no header, More
Information or Play Trailer. Info still opens the info dialog through
`Hub_Spotlight_Button`. Left/Right call `Control.Move(301,∓1)` on the random wraplist,
so Left brings back the previous title and Right the next.

Through 1.12.9, Left did nothing. `CGUIControlGroupList::AddControl` points Play's Left at
the arrow image 314 and gives 314 the grouplist's own `onleft`. It checks that action's
condition once at load, while 301 is still empty. If no condition is met, it treats the row
as wrapping and points 314's Left back at 311, and `CGUIWindow::OnMove` drops the cycle.
Right always worked because the grouplist has an unconditional `<onright>noop</onright>`.
Since 1.12.10 there is a matching `<onleft>noop</onleft>`.

**Preview stage (1.12.8, Rick 2026-10-18 16:35).** A Home preview plays in a
right-anchored 1600×900 box (`home_preview_w/h`, `Background_Video_FlixArt` with params),
larger than the 1280×720 fanart and behind the info panel and rows. Rows never move for a
preview and the focused-row info (logo, ratings, date, length, plot, ends-at) stays up
beside it. New Releases drops `home_premiere_drop` (80px) while 501 has focus so its
posters end ~16px above the bottom edge. The now-playing footer ("Trailer" + progress
ring) hides while `Exp_RixFlix_PreviewPlaying`.

**Random spotlight.** Home is `KEEP_IN_MEMORY` (`GUIWindowHome.cpp`), so a static
spotlight URL is queried once per Kodi run. `Path_RixFlix_HomeSpotlight` swaps the stock
RandomMovies.xsp (which loaded all ~730 movies) for RandomSpotlightA/B.xsp (identical:
random order, limit 30), and Home's onload flips `RixFlix.SpotlightSlot` so every load
changes the URL and re-queries. Rejected: a `videodb://movies/titles/?xsp=` URL (1.12.8
shipped it; the box loaded 726 items in database order because `GetMoviesByWhere` sorts
with the caller's SortDescription, not the xsp's) and a `?seed` on the special:// path
(CURL does not split options for special://, so the file lookup fails).

**Landscape New Releases (1.12.10, Rick 2026-10-18 21:29).** New Releases cards are 16:9
landscape art at 432×243 (`Layout_Landscape`, filled, with no labels or badges), so
they cover less of the preview. The focused cards keep the 1.12.9 bottom edge at y1060.
That needs `home_premiere_drop` = 544 − card height (301). The row height follows the card
(1012), which keeps Recently Added at y1085, just below the screen.

**No flash on focus change (1.12.10).** `CDirectoryProvider::OnEventPublished` re-queries
every provider sorted `none`, `lastplayed`, `dateadded`, `playcount` or `lastused` on each
player OnPlay/OnStop. Every New Releases preview starts and stops a player, so each focus
change re-ran all five provider rows and the spotlight. Each row then got new list items,
its cards were rebuilt and their art reloaded. The screen flashed through the loading
skeletons, and the spotlight re-drew 30 random titles, so Left could not find the previous
one either. RixFlix provider rows (`widgets_row.xml` `widget_sortby`) and the Home
spotlight (`Sort_RixFlix_HomeSpotlight`) now sort by `playlist`, which player events
ignore:
- Provider items all have program count 0, and `SortUtils` uses `std::stable_sort`, so
  provider order is kept.
- `CSmartPlaylistDirectory` numbers the random .xsp results in query order, so the random
  draw is kept.

Real playback still refreshes the Continue rows, because saving a resume point or playcount
announces VideoLibrary `OnUpdate` (`SaveFileStateJob`). That invalidates any provider holding
video items.

**Residency.** Every row still holds at most 15 items. More cards are on screen,
though: about 5.4 New Releases posters (was ~3 landscape cards), 6.7 per poster row,
and part of a second row. That needs a fresh `rixflix-ui-bench.py --residency` run
before the layout is accepted (Rixflix `docs/home-theater.md`).

`python3 scripts/validate_cinema.py` asserts this geometry, the Home include mapping,
poster-only New Releases, plain Categories, the Play-only spotlight with Left/Right
walking 301, the preview stage, footer and the random spotlight query.

# Home without the nav bar — 1.12.11

Rick, 2026-10-18 22:40 and 23:43: Recently Added becomes a landscape preview row like
New Releases. The header stays up on the spotlight. The Search / Home / Settings bar goes,
because RixFlix is only movies and TV and Back always ends on Home.

**Navigation.** Up from the spotlight runs `opensearch.py`, which opens search with its
keyboard. Back on the spotlight stays on the spotlight. It used to walk hidden
button 300 → 303 → `ActivateWindow(1170)`. At 22:52 a Back on the resume menu fell
through that chain: Options opened during the menu's close animation ("ignoring
action 92"), and the TV showed black while the remote made navigation sounds. 303 now
also refuses to open 1170 over any modal dialog. Down off the last Home row opens
Options (1170, the old gear), via the `ondown` param of `Hub_Widgets_Grouplist`; search
rows keep the bumper. The header lives in dialog 1182, which cannot read Home's focus.
It keys on `Window(Home).Property(TMDbHelper.WidgetContainer)` = 301, which only the
spotlight sets. The bar's group is hidden while Home is visible.

**Header.** `System.Time • temperature • AQI n`. The number takes its EPA band colour.
The Rixflix service owns `Window(Home).Property(RixFlix.AQI)` and `RixFlix.AQI.Level`
and clears them when stale, so an empty property draws nothing.

**Recently Added.** Style `PremiereFull` is `List_Premiere_Row` (432×243) at the standard
1140px row height. Only the first row may be short: Kodi scrolls the first focusable
row to 0, and a short second row lands 128px higher or lower depending on direction.
Rows 501 and 502 both drop by `home_premiere_drop`, so focused cards end at y1060 and
Continue Movies stays below the screen. One skin timer serves both rows, keyed on
`Container.ListItem` (the focused list on Home). Two per-row timers race: moving
502 → 501 runs 501's onstart, then 502's onstop clears the selection.

**No bounce.** Spotlight → 501 runs the row drop together with group 400's 440px
`Exp_Hubs_Spotlight_SlideDown` slide. 1.12.10 paired a 300ms cubic in-out drop with that
400ms quadratic slide. The sum dipped and climbed back (Rick: "janky bounce"). The drop
now uses the same time and tween, as two one-way (`reversible="false"`) animations like
400's. A reversible animation replays its curve mirrored on the way back and bounces
again.

**No busy flash.** RC1 raises DialogBusy on every VideoPlayer open
(`CGUIDialogBusy::WaitOnEvent`), so each preview start flashed the bottom-right spinner.
`Exp_RixFlix_PreviewStarting` hides it while the service's `LocalTrailerActive` is set and
no `LocalTrailerCancel` is pending. Real playback cancels the preview first, so it keeps its
spinner. The poster skeleton flash itself came from the display: `adjustrefreshrate=2`
resets GLES on every player stop, and the resize frees every texture. That fix is the
Rixflix theater profile's `On start` (3).

**Toast card.** `Furniture_Busy_Main` draws an opaque `rix_cinema_surface` rounded card
under any labelled bottom-right toast. An example is jellyfin-kodi's "<title> / …"
progress (DialogExtendedProgressBar), which could not be read over posters. Label-less
DialogBusy stays a bare spinner.

`validate_cinema.py` asserts the drop curves against the spotlight slide, the
PremiereFull mapping and both bottom edges, the Up/Back/Down routes, the header and bar
visibility, and an opaque toast card.
