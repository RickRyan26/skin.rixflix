# Cinema presentation — 1.10.0


## 1.12.25: the seek bar stays up through a network seek

Rick, 2026-10-20 22:48: fast forward and rewind are the jankiest piece left. The theater debug
log of eight seeks on 6 Underground showed `DialogSeekBar` closing about 2.8 s after the
press, while the demuxer was still refilling (a cache miss costs the server's first byte,
0.6-3.6 s, plus 1-1.5 s of demux seek and decoder resync). Kodi then re-opened the bar the
moment the seek completed. The bar's `Player.HasPerformedSeek(2)` is now `(3)`, the same as
the chapter label already used, and so is the seek-offset label at `Includes_Labels.xml`
~1004. The bar no longer flickers off and back on during a refill. The full measurements
are in Rixflix `docs/home-theater.md` ("Seek refill anatomy").
## 1.12.24: a motion debug strip on Home, for the probe only

Spotlight <-> New Releases still jittered on 1.12.23. A burst strip (one key, then ten
TakeScreenshot builtins that Kodi runs one per main-loop pass, Rixflix
`am9/rixflix-home-motion-strip.py`) showed the cause is inside one motion, not between runs.
Frame 3 of every burst puts the rows one frame back toward their start, and frame 4 returns to
frame 2's position to the pixel (Down 862 -> 900 -> 862, Up 910 -> 874 -> 912; card top in
1080p units). That is `CAnimation::Animate`'s arithmetic for a reversible effect whose condition
flips for one frame: it runs one frame the other way, then reverses back from the same amount.
`Home_Motion_Debug` draws each input of `Exp_Hubs_Spotlight_SlideDown` as a green/red cell
(plus focus, WidgetContainer and the active window), hidden unless
`Window(Home).Property(RixFlix.MotionDebug)` is set. The probe sets it for the burst and clears
it after, so a capture names the input that flipped. `validate_cinema.py` asserts the gate.

## 1.12.23: the OSD timeline behaves like Netflix

Rick, 2026-10-20 21:17: with the timeline focused, Up should return to the video without the
timeline and Select should toggle play/pause. VideoOSD's timeline (8200) was a `slider`; Kodi's
slider returns true on Select without acting and has no `onclick` (GUISliderControl.cpp,
`ACTION_SELECT_ITEM`), and Up had no target. 8200 is now an invisible button: Select
`PlayerControl(Play)`, Up `Dialog.Close(videoosd)`, Down the buttons, Left/Right
`Action(StepBack|StepForward)`. Those are the keymap's 10 s steps, so a burst is one network
seek after `videoplayer.seekdelay`; the slider sought a percentage on every press. The progress
bars above still show on `Control.HasFocus(8200)`. MusicOSD keeps its slider.

## 1.12.22: the spotlight Play is white

Rick, 2026-10-20 21:13: the random row's Play button should be white with black text, not red
with white text. Control 311 now focuses to `rix_cinema_paper` with `rix_cinema_ink` text (the
same pair it shows unfocused; the spotlight is hidden whenever focus leaves it, so no state
needs to tell them apart). `validate_cinema.py` asserts the pair and its contrast.

## 1.12.21: no Now Playing card over playing video

Rick, 2026-10-20 19:39 (photo, Fall 2 playing behind Home): the card shouldn't show while video
plays in the background, and its text shouldn't cut off so early. `Furniture_Player` now also
needs `$EXP[Exp_Video_IsNotPlaying]`, the condition the background uses to draw the
videowindow/visualisation, so the card returns on pause or with background video disabled. Its
`Furniture_Busy_FloatingText` passes `divider_visible=false`: the toasts' 320px divider shared a
620px grouplist with the sub-label, leaving it under 300px. The DialogBusy spinner card at a
movie start is unchanged.

## 1.12.18: everything bottom-right sits on the card

Rick, 2026-10-20 16:15 (photo while Die My Love started): the loading spinner and the movie
info to its left read straight over the posters. 1.12.11 had put the opaque rounded card
(`rix_cinema_surface`, `common/box.png`, 24/14px margins) only under *labelled* toasts in
`Furniture_Busy_Main` (DialogExtendedProgressBar, e.g. the addon updater; DialogNotification).
What shows at a movie start on Home is a different pair: `Furniture_Player`, the Now Playing
footer (title, sub-label, play/pause icon in a progress ring, visible on `Player.HasMedia`), and
DialogBusy's RIX spinner (`haslabel=false`, so no card). Now `Furniture_Player` draws the same
card behind its whole 720px band, and a label-less busy dialog draws a 138px card around its
100px ring. `validate_cinema.py` asserts both.

## 1.12.17: rows scroll ease-out again

Rick, 2026-10-20 on 1.12.16: "now every row has jitters on row change and it's even more
extreme." On 1.12.14 he had reported only the two landscape/poster boundaries, so ordinary
rows were fine on the grouplist default (400ms quadratic, Kodi's default ease-out). 1.12.15
moved every Home scroll to in-out to match the 301px lift: each row change then started at
zero speed, crawled for the first ~100ms while the focused card had already lit up, and
rushed through the middle. It read as lag then a jolt on every row. The fix goes the other
way: the scroll keeps the default, and the one move that runs with it (the 301px lift,
Recently Added <-> Continue Movies) eases out on the same 400ms. The lift keeps its 1.12.15
focus key, so the two still start on the same frame. The 139px and 440px spotlight moves stay
in-out: no scroll runs with them (row 501 is already at offset 0).

**Rule:** curves that must match are matched to the grouplist scroll, never the other way.
A scroll curve applies to every row change; an animation curve applies to its one transition.

The same report had a second, separate cause on rows 501/502, in Rixflix
(`context.rixflix.gotoshow/local_trailer.py`, 2026-10-20). Leaving a card with a playing hover
preview stopped the player at once, and Kodi's `CVideoPlayer::CloseFile` runs on the GUI
thread: the log showed `waiting for threads to exit` from 33.999 to 34.216 (≈220ms, mostly
`CAMLCodec::CloseDecoder`), ~40ms into the 400ms scroll. The resident now pauses at the leave
(hides the video via `Player.Paused` in `Exp_Video_IsNotPlaying`; silences audio) and sends
Stop only once focus has been still for the length of a row motion.

## 1.12.16: the spotlight state follows focus

Spotlight → New Releases had no scroll to blame (Kodi scrolls the first focusable row to
0, where it already is). The jitter was a split frame. `ondown` navigation moves focus
synchronously, so the 501 card highlights and the row un-dims on the keypress frame. But
`Exp_Hubs_Spotlight_SlideDown`, which drives the 139px row move, the 440px spotlight move,
the spotlight's visibility and the other rows' 30% dim, read only `WidgetContainer`. Row
`onfocus` sets that through a queued thread message (`GUIControlFactory.cpp`:
`focusActions.EnableSendThreadMessageMode()`), one or more frames later, and later still
when the GUI thread is busy. The expression is now `ControlGroup(310).HasFocus |
Control.HasFocus(301) | [!ControlGroup(602).HasFocus + property==301]`. Inside the
spotlight or the rows, focus decides. Anywhere else (a dialog over Home, hidden refocus
buttons 302/304, other hub windows) the property still decides. `Hub_Spotlight_Visible_Expression`
and the row template's `widgetfade_disable` reference it, so everything flips together.

**Rule for Home motion:** never key a moving or fading element on `WidgetContainer` alone
when the move is caused by focus. Pair it with the focus test, or that element lags the
focus change by the message queue.

Known leftover: Back from a row's first item goes 602 → 302, whose `Hub_Action_Reset` focuses
501 for a frame before 301. That can nudge the spotlight move both ways once. It is
unchanged from before and outside the reported transition.

## 1.12.15: one motion at the landscape/poster boundary; landscape search

Rick, 2026-10-20 on 1.12.14: rows still jitter entering Recently Added from below and
New Releases from above. Lower poster rows sit 301px higher in the viewport than the
landscape rows (`Hub_Home_Rows_Motion`), so Up from Continue Movies is a 396px grouplist
scroll plus the 301px lift reversing. Two things made that two motions:
- **Different frames.** The scroll starts on `GUI_MSG_FOCUSED`
  (`CGUIControlGroupList::OnMessage`). The lift keyed on `TMDbHelper.WidgetContainer`,
  which the row's `onfocus` sets through a queued GUI message (`CGUIAction::ExecuteActions`),
  so it began a frame or two later. Inside 602 the lift now keys on `Control.HasFocus`,
  which changes with the focus message itself. Outside 602 (spotlight, a dialog over Home)
  it still reads the property, so nothing moves when focus leaves the grouplist.
- **Different curves.** The grouplist default `scrolltime` is quadratic with Kodi's
  default ease-out; the lift and the 139px spotlight move are quadratic in-out. (Reverted
  in 1.12.17: see above. The lift eases out instead.) Home's 602
  now scrolls 400ms quadratic in-out (`Hub_Home_Rows_Scroll`; `GetScroller` reads the first
  `<scrolltime>`, and includes resolve ahead of the appended default), so a scroll that
  coincides with either move is one 697px curve, not a fast scroll and a trailing drift.

Rejected: moving the 301px into the landscape rows themselves (a per-row offset plus a
301px spacer). Settled frames match, but the grouplist clip is 16px above the focused cards
only because the whole list moves; a fixed viewport origin exposes the faded previous row
through a 301px band above Recently Added.

Search results use the `Landscape` style (`List_Landscape_Row`), so 2:3 posters no longer
hang over what sits beneath the row.

Rendered smoothness is not provable offline; the AM9 check is Rick's eye on the two
boundaries. `validate_cinema.py` asserts the focus-keyed lift, the in-out scroll and the
landscape search style.

## 1.12.14: isolated Home motion and page-edge navigation

Rick retested 1.12.13 and still saw jitter and a brief stall. The previous 24
fast direction actions only established focus delivery; they did not establish
smooth rendered movement or sustained preview stability.

Home now isolates the spotlight's 440px animation inside its visual group. It
cannot move ancestor 400 and all of the rows beneath it. Home grouplist 602 owns
one 139px reversible spotlight transition, with a static -139px baseline and a
separate -301px offset used only for lower poster rows. The optional ancestor
240px slide is also compile-excluded for Home. Settled row origins remain
940/801/500 and landscape card bottoms remain at 1060. No row height, viewport,
content or visibility changes on the spotlight/New Releases boundary. Kodi's
first focusable child still scrolls to offset zero. The validator enforces motion
ownership rather than matching two independent curves.

Search uses one Results row containing local movies and series, capped at 20
combined items. DefaultSearch-All targets the Rixflix mixed provider with the
committed edit text encoded once. The Rixflix provider and installed shortcut
configuration must be deployed with this version; hiding the TV row would lose
series results and is not the implementation.

Search Back and bottom Down return Home. Options (1170, reached by Down off Home)
returns Home on Back and Up from its top tiles, for all supported tile layouts.
Those routes focus eligible proxy 7900, which arms a timer; the timer closes the
Options dialog when necessary and activates Home after OnMove consumed the key.
Keyboard and inner-dialog Back remain owned by their dialogs. Switching windows
directly inside OnMove would resurrect the earlier teardown/fallthrough bug.

Rick explicitly withheld TV access while using it. Only offline source checks
were run for this revision; rendered jitter and live page edges remain unverified.
The Rixflix activation pin/runtime changes must remain unlanded until he permits
TV work, because its convergence timer would otherwise deploy them automatically.

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

**Spotlight/row motion (1.12.12).** The 1.12.11 pair of non-reversible animations
still snapped when Up/Down reversed before its 400ms move completed. Kodi's
`CAnimation::UpdateCondition` resets a non-reversible effect as soon as its condition
becomes false; the opposite effect starts from its literal endpoint. Matching their
curves did not preserve the partially travelled position.

Both group 400's 440px spotlight slide and group 602's 301px landscape-row drop now
use one reversible 400ms quadratic `inout` effect each. Kodi's `CAnimation::Animate`
retains the current animation amount when reversing; it does not restart at an endpoint.
The symmetric easing makes the opposing curves complements, so their sum travels
monotonically by 139px between spotlight and New Releases in either direction. Both
conditions read `TMDbHelper.WidgetContainer`, which the focused control publishes:
using `Control.HasFocus` for one and the property for the other could start them on
different frames. Recently Added retains the same drop, and preview player state
still cannot move any row. Card sizes and all settled bottom edges are unchanged.

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

# Offscreen spotlight focus escape — 1.12.13

A live pre-restart capture after waking/Back showed Home with `System.CurrentControlId`
301 and `TMDbHelper.WidgetContainer` 301, while the local trailer selection/active
properties were empty. 301 is the offscreen 1×1 wraplist that owns the random spotlight
items. Its normal `onfocus` redirects to visible Play (311), but it had no navigation
routes if a modal/player restore left focus there without replaying that redirect.
The automatic carousel still advances because its condition sees 310 without focus,
which explains live artwork alongside remote sounds and apparently inert input.

301 now has explicit Up/Back → Play and Down → the first available provider row.
Do not substitute `onleft`/`onright` recovery: Kodi's `CGUIBaseContainer::OnLeft/OnRight`
calls horizontal wrapping-list movement first, and `CGUIWrappingListContainer::MoveUp`
and `MoveDown` always return true. Such XML routes never run. Native Select and Info
remain intact because visible Play deliberately focuses 301 and dispatches
`Action(select)` there for plugin paths; replacing its click action would break that
playback path. This provides a deterministic remote escape without a background timer
that could steal focus from a real playback transition.
