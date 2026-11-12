# Cinema presentation — 1.10.0

## 1.15.1: a stage chip on a poster card

Rick, 2026-11-11: Home's Requested row "should use vertical posters". `Layout_Poster` now
draws one 244 px crimson pill (the card is 260 wide) when the item has both
`RixFlix.CardChip` and `RixFlix.RequestKey`, under the focus outline. Only a still-coming
Request card has both, so Continue posters stay bare. Landscape cards keep
`RixFlix_Card_Chip` and its two pill widths.

## 1.15.0: Search on the stage; one card chip; plots that do not scroll

Rick, 2026-11-11: the search results page "needs to be more like the homepage and the
category pages in a DRY way. The row title should be on the far left and the rows should be
closer together", a focused result should show its details as Home does, the TMDb Discover
pop-up must go, and Coming Soon's trailers played "but there's no visual" while its details
had "a vertical marquee".

**Search is the third stage page.** `Search` (Includes_Search.xml) now draws
`RixFlix_Stage_Backdrop`, `RixFlix_Stage_Info` and `RixFlix_Stage_Rows`, the includes a
category page and Coming Soon use. `Search_Stage` holds two `RixFlix_Stage_Row` calls:
Results (list 502, group 702) and Request (list 540, group 541), in grouplist 8500.

| Before | Now |
|---|---|
| "Results" / "Request" headings over the rows, rows 380 px apart | Home's rotated title at x40, rows one pitch (268 px) apart, card tops y552 and y820 |
| Logo only (the field hid the panel) | Home's full panel: logo, facts, source line, plot, "Ends at" |
| Generated `Hub_Combined_Widget` row, 601 switcher, `Search_Request_Row`, `List_Request_Row`, `Layout_Request` | `RixFlix_Stage_List` for both rows; those three includes are deleted |
| Field and header always shown | Shown with the field. A focused row hides them; the page chip reads `Search • <text>` |

- **Field and rows.** The field group is visible while no row has focus
  (`!ControlGroup(8500).HasFocus`). Up from Results returns to it. The Request row's one
  hint ("OK to request • Hold OK for details", or the chip text) sits under the page chip.
- **Rows never hide.** A row whose cards are not for the typed text fades through the stage
  row's `stale` rule, so it always loads (the 1.13.3 rule). Request sits in the second row.
  When the finished search found nothing in the library, a conditional slide moves it up one
  pitch (`Exp_RixFlix_Request_Raised`). Focus no longer raises it: both rows are on screen.
- **Ids kept.** 3000, 502, 540, 541, 7900 and every Down/Up route from the field are
  unchanged. `Exp_RixFlix_Search_Loading` now reads only `SearchCompleted` and list 502.
- **No preview on Search.** The backdrop is the stage's, but the hover timer still covers
  Home, a category page and Coming Soon only.

**TMDb Discover is gone from Search.** Up on the field ran TMDb Helper's `user_discover`
dialog, and a switcher item did the same. Both are deleted with the two window `onload`
lines that seeded its folder path. Up on the field is `noop`.

**The Coming Soon preview was black.** `RixFlix_Stage_Backdrop` drew an opaque full-screen
image and then the video window. Kodi 22 draws opaque textures in a first pass that writes
depth, and `CGUIVideoControl::Render` punches the video hole with a quad at the far plane
(`DrawQuad(region, 0, …, -1.0f)`), which loses the depth test to any opaque texture behind
it. Home has nothing behind its video window, so only the stage pages played sound over a
black box. The base image is now visible only while `Exp_Video_IsNotPlaying`.
Screenshots cannot show this: the AM9's video plane is not in a Kodi screenshot. It needs
eyes on the TV.

**No vertical marquee.** The skin's default textbox auto-scrolls. A card with no library
row (Coming Soon, a Request card) used the two-line fallback box, so its plot crawled.

- All five `RixFlix_Home_Plot` textboxes set `autoscroll` false.
- A card with an empty DBID draws no quality line (64 px, no longer reserved) and no
  "Ends at" (60 px). Its plot takes that room: 200 px (5 lines) under a heading, 240 px
  (6 lines) without (`max_h_free_heading`, `max_h_free`).
- Those boxes read `RixFlix.CardPlot`, which the provider cuts to whole words + "..." with
  the resident's `fit_plot` (provider 1.10.0). `ListItem.Plot` stays whole for the Info page.

**One card chip.** `RixFlix_Card_Chip` (Includes_Layouts.xml) is the one corner chip of a
landscape card. `Layout_Premiere` asks for it (`chip` true); the provider names it in
`RixFlix.CardChip`: "New Episode" on a series the household was caught up on, "Requested" /
"In library" on a Request card. It draws under the focus outline. `RixFlix.RequestChip`
remains for the Info page's button and the hint. The chip keeps 1.14.10's two pills: 176 px,
or 288 px when the provider sets `RixFlix.CardChipWide` (a stage with a date).

Source checks: `scripts/validate_cinema.py` PASS (stage rows, routes, chip, backdrop order,
plot boxes). Written without a render: the theater did not answer on 2026-11-11 16:30 PST.
Native proof is recorded in Rixflix `docs/home-theater.md`.

## 1.14.4: the Request row loads after Results, not beside it

With both rows keyed on SearchText, every letter started two Python interpreters at
once on the AM9. Search smoke keypress-to-results rose from 0.75-1.0 s (row not
loading) to 1.0-1.3 s, and the Request job itself read 230-470 ms. `Path_RequestSearch`
now takes `RixFlix.SearchCompleted` as its refresh token: the provider publishes that
when the Results search for the text is done, so the Request lookup starts then. The
provider still reads SearchText for the query and drops a superseded run. Provider
1.9.2 drops its 150 ms head-start wait, which this ordering replaces.

## 1.14.3: the first search shows its posters while you type

Rick (2026-11-10): on a first search nothing appeared under the keyboard; closing it
showed the results at once. Later searches worked.

- **Cause.** The Results row shows only while its switcher item (list 601) is visible,
  and that item required `Control.GetLabel(3000)` to be non-empty. Edit 3000 is the
  Search field; Kodi writes the keyboard's text into it only when the keyboard closes.
  With an empty field (a first search) the item, the "Results" heading and row 502 all
  stayed hidden. With an old query in the field they showed, which hid the fault.
- **Proof.** `search/typing-first-open.png` (field seeded) draws the row;
  `search/typing-paused-behind.png` (field cleared first) does not, though the provider
  logged `local query='AB' results=20`. The paused video was not the cause.
- **Fix.** The item is also visible when `Window(Home).Property(RixFlix.SearchText)`,
  the live text, is non-empty (`shortcuts/generator/data/parts/search_item.xmltemplate`).

## 1.14.0: the stage (category pages and Coming Soon)

Rick, 2026-11-11: the category sub pages and Coming Soon must "DRYly replicate the homepage's
landscape posters rows format with the video information above", and Coming Soon must use the
pulsing RixFlix loading indicator. Both pages are now one definition in
`1080i/Includes_CategoryHub.xml`.

| Include | What it draws |
|---|---|
| `RixFlix_Stage_Backdrop` | The focused card's fanart in Home's 1600×900 preview box, with Home's preview video window under it |
| `RixFlix_Stage_Info` | Home's `Info_Panel` for the focused card: logo, facts, source line, plot, "Ends at" |
| `RixFlix_Stage_Rows` | The row stack, exactly two Home pitches tall |
| `RixFlix_Stage_Row` | One `List_Premiere_Row`, Home's own landscape list |
| `RixFlix_Category_Row` | A genre row: `RixFlix_Stage_Row` plus the genre's visible, stale and content rules |
| `RixFlix_PageLoading` | The pulsing wordmark. Coming Soon's "Loading upcoming trailers…" sentence is gone |

A category page is fourteen `RixFlix_Category_Row` calls of one line each; Coming Soon is four
`RixFlix_Stage_Row` calls. The fourteen hand-copied row blocks (and four more in Coming Soon) are deleted.

**One panel, one backdrop.** Bare `Container.` is the window's focused container
(`CGUIInfoManager::GetActiveContainer`: a non-media window uses its focused control). So one
`Info_Panel` and one fanart image follow whichever row has focus. Home needs a panel per row because
its rows are generated; a stage page does not. The backdrop reads the card's own art, so it does not
wait for TMDb Helper's service monitor, and Coming Soon (window 1138) needs no entry in
`TMDbHelper.UseLocalWindowIDs`.

**Geometry.** The viewport is two pitches (536px) at y532. Card tops are y552 and y820, and the
second row ends at y1063, where the old four-row page's last row ended. The panel uses Home's
poster-row budget (tagline + two lines, "Ends at" bottom y500), which clears the first card. Home's
landscape rows use the five-line budget (bottom y580) because their cards start at y644; the stage
trades two plot lines for a second full row. `GUIControlGroupList` scrolls a focused child to a
viewport edge, so only a whole number of pitches stops on a row boundary; that rule is why the
viewport is two rows and not Home's one row plus a slice.

**Plot source.** The resident service publishes `RixFlix.Plot.RowPoster` for a library card on window
11101, as it does on Home. A Coming Soon card has no library row: the provider tags it media type
`video`, so `RixFlix_Home_Plot` falls back to the card's own `ListItem.Plot` and the 64px source line
is not reserved. Its bold line is the provider's tagline ("Movie · Coming December 5").

**Trailers rotate in over the poster.** The hover timer (`rixflix_local_new_release_trailer`) now
covers three surfaces: Home 501-504, a category page (grouplist 8100) and Coming Soon (8810). After
the resident's 2.5 s dwell, a trailer the box has cached plays in the backdrop's video window, and
`Background_NotVideo` fades the fanart out over it. A card with no cached trailer keeps its fanart.
A library card is selected as `DBTYPE-DBID`; a Coming Soon card by the provider's
`RixFlix.TrailerKey` (`yt-<YouTube id>`). `DialogBusy` forwards arrows and OK to all three windows
while a preview opens; a builtin's window argument is the skin's id (`1101`), a condition's is
Kodi's (`11101`).

**OK on a Coming Soon card.** `scripts/rixflix_trailer.py` first looks for the trailer in the box
cache and plays that file fullscreen with no resolver. If this card's preview is already playing,
the same player goes fullscreen (the resident promotes it); Back stops it and returns to the page.
Only an uncached trailer is resolved through yt-dlp. Detail: `docs/trailer-playback.md`.

**Not verified live.** The theater had a paused movie when this landed (2026-11-11 01:00 PST), so
no deploy or screenshot was possible. `validate_cinema.py`, `check_local_trailer_timer.py` and
`check_trailer_handoff.py` pass. The first idle deploy's Coming Soon proof and category smoke are
the live acceptance.

## 1.13.3: the Request row loads on every query

On the theater box the Request row (list 540) stayed empty. The Kodi log showed the
provider's `request_search` running only twice in a whole search smoke, and not once
while a viewer typed five letters, although the Results row ran for every letter.

- **Cause.** The row and its group 541 were `<visible>` only when list 540 had items for
  the typed text. Kodi does not load the content of a hidden container, so after the
  first empty answer the row never asked again.
- **Fix.** Neither carries a `<visible>` now. Group 541 fades to 0 while
  `Exp_RixFlix_Request_Ready` is false, so the list always loads. Every route into 540
  already requires `Exp_RixFlix_Request_Ready`, so a faded row cannot take focus.
- **Rule.** Never key a container's visibility on its own items.

## 1.13.2: Categories splash covers the full screen

The Categories background was lifted 160px but retained its 1080px height,
leaving the bottom 160px uncovered. Its image now extends to 1240px, so the
lifted rectangle ends at the screen bottom. Kodi scale fills that rectangle
with proportional cropping. The logo stays above the cards; the existing
startup splash already fills its screen. No new texture or resident control.

## 1.12.76: fix the active combined Search control

The 1.12.75 native retry still failed repeated Down. The earlier fix changed the
standard-row template, but the deployed generated include uses Hub_Combined_Widget.
Its Search-specific Down still targeted Home (7900). Change that active control
to retain its own result on Down and return directly to edit 3000 on Up. Back
retains the Home target. The cinema validator now inspects both row variants;
Rixflix's live proof records the generated include and active variant as evidence.

## 1.12.75: search navigation survives the parent grouplist

The first idle theater deployment of 1.12.74 failed the native repeated-Down
check. Its numeric row target was overwritten when the parent grouplist added
the row. Kodi explicitly preserves built-in navigation actions in
[CGUIControlGroupList::AddControl](https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GUIControlGroupList.cpp#L284).
Use SetFocus on Down to retain the result and on Up to return directly to edit
3000. The native Rixflix search smoke owns the live proof and focused-card capture.

## 1.12.74: retain search text and make result focus clear

Rick reported that returning Up to Search lost the query, and the first result did
not look ready to open after Down closed the keyboard. Search no longer replaces
the live query from the native edit on window load. The companion `opensearch.py`
restores the last live query into that edit before opening the keyboard, including
the text from a cancelled keyboard. Search's focused landscape card adds a solid
white outline and shows “OK to open”. Down on the sole results row keeps the same
card selected; Back still returns Home and Up still returns to the field.

## 1.12.50: a Down while results load lands on them, never Home

A commit leaves results row 502 empty for the ~1.3 s it takes to load. On the search field,
Down with 502 empty meant "no results, go Home" (7900), so the Down-Down that 1.12.49
invites (or a held Down) threw the viewer back to Home mid-search. Now, while
`Exp_RixFlix_Search_Loading` is true, Down only sets `Window(Home).Property(RixFlix.SearchDown)`.
The `rixflix_search_down` timer then moves focus to 502 once it has items, if focus is
still on the field. It stops without moving focus when loading ends empty, when the viewer
moves, or after 5 s. The empty-results Down still goes Home once loading has finished. The
timer inlines the loading expression because `Timers.xml` cannot use `$EXP`. Search's
`<onunload>` clears the property. `validate_cinema.py` asserts both 1.12.49 and 1.12.50.
There is only one results row (`DefaultSearch-All`, movies and shows together), so 502 is
the only target: a TV-only match also lands there.

## 1.12.49: Down off the keyboard's bottom row runs the search

Rick (2026-10-31): Up from Home opens the search keyboard, and Down from its bottom
button row (Done, Cancel, Shift, Caps, Symbols, IP, Space, Backspace, Left, Right)
should close it and search. That row had no `<ondown>`, so Down did nothing there. Each
of its ten keys now runs `SendClick(300)` on Down. 300 is Kodi's `CTL_BUTTON_DONE`, whose
click calls `OnOK()` (`GUIDialogKeyboardGeneric.cpp`), so this is exactly a Done press: it
commits the term once and the search window shows the results. The key runs only while
the search window (11105) is under the keyboard. Other keyboards, such as settings
and passwords, keep Down as a no-op, so a stray press cannot submit
their half-typed text. `SendClick` reaches the topmost modal dialog, which is the keyboard.
Because the dialog doesn't special-case Down, an `<ondown>` made only of built-ins has no
fallthrough here. The Back-handler rule applies only to window switches.

## 1.12.48: Continue Movies sits one gutter below Fresh Shows

Rick (2026-10-27, photo of the TV): an extra-large gap between Fresh Shows and Continue
Movies. Each Home row is two grouplist children, a label spacer (`labeltop`) and a
viewport-height list, so the distance from one list to the next is
`viewport + labeltop(next)`. Landscape rows use -882 (268px pitch, 25px gutter); poster rows
kept -754, so the first poster row after Fresh Shows sat 128px lower (peek at y1040 instead
of y912). Rixflix's row JSON now marks Continue Movies `widget_labeltop: Premiere`, which
maps it to `home_premiere_label_t`. Focus positions are unchanged: a viewport-height list
always scrolls to its own offset in both directions, and the spacer only moves the row while
it is unfocused. Continue Shows and Categories keep the poster pitch.

## 1.12.47: tighter New/Fresh rows and a fully visible final card

Rick (2026-10-26) requested the next row peeking below focus and no clipped final
item. Landscape rows now have a 268px pitch (243px artwork + 25px gutter), using
style-specific label tops and viewport-height lists in both directions. The first
row bumper cancels its label top. Their focused cards end at y887, matching poster
rows; the next landscape row starts at y912 and Continue Movies peeks in at y1040.
Home motion uses a 312px spotlight transition and 128px poster lift. The four-row
preview membership and animation curves remain the same.

The 448px landscape stride fits four complete cards from x80. A movement range of
4 admitted a fifth focus slot at x1872; 3 ends at x1856, inside the right margin.
Source: [Kodi fixedlist](https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GUIFixedListContainer.cpp)
and [grouplist](https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GUIControlGroupList.cpp).


## 1.12.46: no Now Playing card while paused

Rick's 2026-10-26 Love Language photo shows the title, director and pause icon on the
bottom-right card over Home. This is `Furniture_Player`; its existing
`Exp_Video_IsNotPlaying` condition deliberately includes pause, so the earlier preview
exclusion cannot hide it for a paused movie. The group now also requires
`!Player.Paused`. The full-screen pause title and timeline remain in `DialogSeekBar.xml`;
the Home footer no longer covers the rows during pause.

## 1.12.45: no Now Playing card around a hover preview

Rick's 2026-10-26 19:24 photo: a wide dark card bottom-right over the rows with nothing in
it but the play icon. It is `Furniture_Player` (720px + the 24px card margins; the icon is
`Image_NowPlaying_PlayPause`'s `play2.png`, not DialogBusy's RIX badge). Its preview guard,
`!$EXP[Exp_RixFlix_PreviewPlaying]`, needs `Player.HasVideo`, and a hover preview has
`Player.HasMedia` without video while it opens and while it closes; `Player.Title` is empty
then, so the card drew blank. It now also requires
`String.IsEmpty(Window(Home).Property(RixFlix.LocalTrailerActive))`: Rixflix's resident sets
that at its play call and clears it only after Kodi's terminal callback, so it covers the
whole preview lifetime, and a real movie start releases it on the next 50 ms tick.
`validate_cinema.py` pins the guard. Rixflix `docs/home-theater.md` has the log evidence
and the 2.5 s dwell that removes the open/close churn behind it.

## 1.12.44: four landscape New/Fresh rows

Rick (2026-10-26): "break the (New Releases and Recently Added) up into 2 rows each; New
Movies, New Shows & Fresh Movies, Fresh Shows", with no title on two of them. Rixflix's
row JSON now puts those four first (501 `Premiere`, 502-504 `PremiereFull`), then Continue
Movies 505, Continue Shows 506 and Categories 507; the provider keeps them single-kind and
disjoint. Every landscape row behaves as 502 always did: the one local-trailer timer keys
on focus in 501-504, and the 301px lift exempts 501-504 (focus inside 602, or the queued
`TMDbHelper.WidgetContainer` outside it), so all four drop by `home_premiere_drop` onto
the spotlight stage and the poster rows stay below the screen. `check_local_trailer_timer.py`
now pins the whole four-row focus group in start and its negation in stop (its old
`!Control.HasFocus(501)` probe had matched nothing since the 1.12.11 `![…]` stop).

## 1.12.41: Home Play returns to the existing video

Home spotlight button 311 labels itself **Return to video** when
`Window.IsActive(Home) + Player.HasVideo + !$EXP[Exp_RixFlix_PreviewPlaying]`.
`Player.HasVideo` also covers paused video; testing `Player.Playing` would strand a
paused movie behind Home. The existing preview expression excludes hover trailers.
This branch only calls `ActivateWindow(fullscreenvideo)`, so it changes the window
without stopping, starting, resuming or toggling the player.

Every original onclick has the inverse guard, including trailer cleanup and focus
restoration: returning to the movie must never select/play the spotlight title.
Kodi's [`CGUIAction::ExecuteActions`](https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GUIAction.cpp)
collects matching actions before executing any of them, so opening fullscreen does
not re-evaluate the Home guard and fall through into the spotlight branch.
Without a real background video, the original Play/folder label and ordered spotlight
actions remain intact. Other hubs, Back, spotlight Left/Right and widget counts keep
their existing contracts. Native window activation follows Kodi's
[built-in function contract](https://kodi.wiki/view/List_of_built-in_functions).
`python3 scripts/validate_cinema.py` is the source structural check; device proof of
playing and paused returns belongs to the parent pin/installer session.

**1.12.42: fit the full label.** Pillow measures `Return to video` in the bundled
`fonts/Inter-Bold.ttf` at 28px (`font_main_bold`) as 207.78px. CoreELEC Kodi
[`CGUILabel::GetMaxWidth()` at 4665ec22](https://github.com/CoreELEC/xbmc/blob/4665ec22/xbmc/guilib/GUILabel.cpp#L226-L230)
subtracts twice `textoffsetx` from the button width: the former 240px caller with
24px offsets left only 192px, truncating the unfocused label and scrolling it on
focus. Only Home spotlight button 311 now requests 280px, leaving 232px of text
space (24.22px beyond the measurement). The shared button template, exact label,
native return action and spotlight arrow navigation retain their existing contracts.


## 1.12.25: the seek bar stays up through a network seek

Rick, 2026-10-20 22:48: fast forward and rewind are the jankiest piece left. The theater debug
log of eight seeks on 6 Underground showed `DialogSeekBar` closing about 2.8 s after the
press, while the demuxer was still refilling (a cache miss costs the server's first byte,
0.6-3.6 s, plus 1-1.5 s of demux seek and decoder resync). Kodi then re-opened the bar the
moment the seek completed. The bar's `Player.HasPerformedSeek(2)` is now `(3)`, the same as
the chapter label already used, and so is the seek-offset label at `Includes_Labels.xml`
~1004. The bar no longer flickers off and back on during a refill. The full measurements
are in Rixflix `docs/home-theater.md` ("Seek refill anatomy").
## 1.12.32: the Play <-> New Releases jitter was Kodi's broken quadratic in-out

**Cause.** Both `SlideDown` slides, the rows' +139 (`Hub_Home_Rows_Motion`) and the
spotlight's +440 (`Hub_Spotlight_Motion`), used `tween="quadratic" easing="inout"`.
Kodi's `QuadTweener` `EASE_INOUT` (`xbmc/guilib/Tween.h`) is wrong: the first half
returns `change * t^2` with no `/2`, so it covers the whole distance by the midpoint. The
second half returns `change * u * (2 - u)` with no `change/2` offset, so it starts again
from the beginning. Every 400 ms slide therefore reached its end at 200 ms, snapped back
to its start, and eased out a second time. That snap is the backward step, and it appears
in both directions and only on the moves that run these two slides. Row-to-row moves use
the grouplist scroll's default ease-out and were always smooth. This is not a condition
flip, a stale transform or the background art.

**Proof.** The 1.12.31 window-level copies (theater receipt 81146e57081ab571, bar x
against the latch clock): Up, `SlideDown` quadratic in-out read 58, 233, 934 at 41, 82,
164 ms (exactly 1390·(t/200)²), then **68** at 205 ms and 946 at 287 ms. The same slide
with `linear` was monotonic: 142, 285, 570, 712, 997. A quadratic in-out copy on
`ControlGroup(310).HasFocus` stepped back the same way, so the condition plays no part.

**Fix.** Both slides are `tween="sine" easing="inout"`, which is correct in Kodi
(`change/2 * (1 - cos(pi t))`) and is the closest curve to the in-out the comments call
for. `validate_cinema.py` asserts the two slides and fails on any quadratic in-out
animation or effect anywhere in `1080i/`. `cubic` in-out is also correct if a steeper
curve is ever wanted.

**Cleanup.** The probe-only A/B gates are gone: `RixFlix.MotionNoArt`,
`RixFlix.MotionSpotlightStatic`, `RixFlix.MotionPair` and the 1.12.31 tween bars. The
debug cells and latch bars stay. They draw nothing unless the probe sets
`RixFlix.MotionDebug`, and the strip reads them.

## 1.12.31: the SlideDown slide at window level

The 1.12.30 probes inside group 400, group 500 and the Info panels' parent all stayed on
time in the backward frame (theater receipt ae4a448f6137277f, Up 823, 840, 910, **824**,
912), so no ancestor subtree is stale and the probes are gone. What the rows and Play
share, and the latch bars don't, is the slide itself: reversible, quadratic in-out, 400 ms,
on `SlideDown`. Three copies of it now run horizontally at window level (1390 px, ten
times the rows' 139): on `SlideDown` with in-out quadratic, on `SlideDown` with linear,
and on `ControlGroup(310).HasFocus` with in-out quadratic. Whichever one steps back with
the rows separates the condition from the tween.

## 1.12.30: subtree probes for a stale transform

The 1.12.29 pair kept the backward frame (theater receipt 8c21a2ee37ae2f27), so the
reversible state machine is not the cause. In every run the step is about one frame of
motion against the direction of travel (Down 862, 900, 862; Up 910, 874, 912), and it hits
only the spotlight Play and the rows. The background and the window-level latch bars stay
current in the same frame. That is what a subtree rendered from last pass's cached
transform would look like. Kodi's default dirty-region mode 3 redraws the full viewport,
so stale pixels are ruled out. The 1.12.28 bar now also sits inside group 400 (y650/670),
group 500 (y700/720) and the Info panels' parent (y750/770): the Down condition (F501) and
then the Up one (G310). It is pure green and gated by `RixFlix.MotionDebug`. In the
backward frame, a probe that trails the window-level bars names its subtree.
`validate_cinema.py` asserts the probes and their gate.

## 1.12.29: a reversible-versus-pair A/B for the SlideDown slides

The 1.12.28 latch bars ruled out a condition flip. On Up, the `SlideDown` bar shares the
slides' own cached InfoBool and never resets, and on Down `G602` (the term that holds
`SlideDown` false inside 602) never drops. The timeline the bars give (0.4 px/ms since
focus) puts the backward frame about 205 ms into the move in every burst
(theater receipt 044c1c235aab5e30). In that frame the rows and the spotlight Play render
at their start offsets, and the frames after it lag the curve, while linear
non-reversible slides evaluated in the same pass stay on time. So the reversible state
machine of the two slides is disturbed without its condition changing. Each slide now
also exists as a non-reversible pair (the `Hub_Spotlight_Content_Slide` pattern), selected
only while `Window(Home).Property(RixFlix.MotionPair)` is set. The probe A/Bs it in one
deploy. `validate_cinema.py` asserts the pairs and the gate.

## 1.12.28: latch bars for a one-frame flip

The 1.12.27 A/B kept the backward frame with the art hidden and with the spotlight held
visible, so neither lead is the cause. The frames themselves show that, in that frame, the
rows and the spotlight Play (the two `Exp_Hubs_Spotlight_SlideDown` reversible slides, and
nothing else) step back to an earlier position, then carry on from it: the shape
`CAnimation::Animate` gives when its condition flips for one tick and flips back. The cells
can't see that: a 4K `TakeScreenshot` stalls the GUI about 83 ms, so about two 24 Hz frames
pass between captures. The strip now carries twelve latch bars under the cells (rows 30px
apart: F501, !SlideDown, G310, SlideDown, G602, !G602, !G310, F301, !F301, WC301, !WC301,
F311). Each one is a non-reversible conditional slide at 0.4 px/ms that snaps to x=0 when
its condition fails, so a bar that trails its reference in a later frame dates the flip
and names the input. They live inside the `RixFlix.MotionDebug` group, and
`validate_cinema.py` asserts the latch include and its count.

## 1.12.27: A/B switches for the motion strip

The 1.12.26 cells showed no input change in the backward frame, and a control burst on
501 -> 502 in the same run was monotonic, so the reversal is real and belongs to this move
(Rixflix `docs/home-theater.md`, "Burst strips and the debug cells"). The two things only
this move does at that frame each get a switch the probe can flip at runtime:
`Window(Home).Property(RixFlix.MotionNoArt)` hides the background art control (an image
that isn't processed loads no texture), and `RixFlix.MotionSpotlightStatic` keeps the
spotlight group and its info visible on the rows. With neither set, nothing changes.
`validate_cinema.py` asserts both gates.

## 1.12.26: a second line of motion debug cells

The 1.12.24 cells (receipt `19d05f526bf66e0f`, 1.12.25) held steady through the backward
frame, and `SlideDown`, focus and WidgetContainer never flipped. Yet the rows *and* the
spotlight info both stepped back one frame, while the background crossfade, which runs on
an accumulated delta, kept advancing. The second line draws the next-order inputs:
the spotlight's visibility expression, 301/501 `NumItems`/`IsUpdating`, the visibility of
310 and 501, the 301px lift condition and `Exp_Hubs_SlideInfo`. It sits at y130 under the
same `RixFlix.MotionDebug` gate.

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


### 2026-11-04: local search while typing

Edit 312 and edit 3000 publish `RixFlix.SearchText` with `$ESCINFO`. The mixed
provider reads that Home property verbatim; `live=1&q=...` is only Kodi's URL
refresh token, never parsed as user text. This preserves ampersands, plus signs,
quotes, commas, literal percent escapes and Unicode without encoder plugin jobs.
Empty and one-character values publish an empty directory. Each returned item
carries its query identity; both row layouts hide mismatches and Down cannot
focus a stale row. The completed property also covers an empty result directory.
Kodi serializes and coalesces directory jobs (4665ec22 DirectoryProvider.cpp);
an older job can complete but its items cannot be shown for a newer query.

Search's keyboard uses 60% scale at the upper left and no dim overlay, leaving
the landscape Results row exposed below. Other keyboard dialogs keep their size
and dim overlay. Down off any bottom key still closes the keyboard onto Search;
page Back goes Home and keyboard Back first dismisses the keyboard. Discover,
autocompletion and both encoder content jobs are disconnected from live input.


### 2026-11-04: compact Search keyboard

Rick asked for the search popup to shrink to essentials and lose its right-hand
suggestion list. Search now resolves a dedicated **880 × 384** panel at (80,64),
with its text field and a three-row QWERTY grid: 26 letter keys plus Delete, Space,
123/ABC and Browse, **30 buttons total**. The number/symbol layer reuses those
letter positions; no extra utility bank, side list, dim overlay or scaled text.
Bottom-row Down closes onto Search, Browse does the same, and Back dismisses
the keyboard. Initial search focus is Q.

`DialogKeyboard` resolves exactly one include tree per opening. Non-search
password/settings dialogs use the complete pre-live-search `DialogKeyboard_Full`
layout. Never load two hidden keyboard trees with duplicate native IDs. Search
character IDs **400..425** deliberately avoid Kodi's auto-labelled **100..179**
range: pinned `GUIDialogKeyboardGeneric::OnClickButton` inserts the description
of any unreserved button below 500. Buttons 8/32/300/304 keep native Delete,
Space, Done and Symbols behavior. Both IME labels 313/314 still exist off-screen:
**native OnInitWindow dereferences 314 unconditionally**, so removing it crashes
Kodi even though this English search panel has no IME choices.

Kodi `CGUIWindow::NeedLoad` tracks include condition values, so switching from
Search to a password/settings keyboard reloads the correct control tree rather
than reusing whichever one was opened first. Generic layout XML is identical to
skin 1.12.50 (`d0aa5c56`), except for its include name.

The live text handler also excludes `System.HasHiddenInput`: if an add-on ever
opens a password prompt over Search, its input must not become search text or a
provider log entry. This is checked at text-change time: Kodi's hidden-input
infolabel becomes true only after the keyboard is active, so it is unsuitable
as an include-load condition for choosing the keyboard tree.

### 2026-11-05: rows that load but stay black, and Down onto the first result

Skin 1.12.57 hid stale hub rows with a conditional `fade start="0" end="0"`. For a zero-length
effect, `CAnimation::Calculate` applies the end while the condition holds and the **start** once it
clears (`VisibleEffect.cpp`), so every row stayed at alpha 0 with its items loaded: the page read
"Loading genres…" and then nothing. Use `start="100" end="0"`. No infolabel exposes a control's
alpha, so the live proof of a hub is a screenshot, never `Control.IsVisible` or `NumItems`.

Down off the compact keyboard's bottom row now arms `RixFlix.SearchDown` before native Done. The
`rixflix_search_down` timer waits until the keyboard has closed, then focuses the first result, or
stays on the field if there are none. The hub's `rixflix_category_ready` timer retries each second,
because a row accepts focus only once it is visible and loading.

## Category page layout (1.12.64)

Rick (2026-11-06, photo of the TV): show as much as possible, landscape instead of posters, Home's row
spacing with row titles on the left, and the category title fixed in a card top right. The poster page
showed 12 titles and clipped its first row; this one shows 16 full cards plus the start of a fifth in each row.

**Rows.** Each row is `List_Premiere_Row`, Home's own landscape list: 432×243 art, the 16px card gap, the
same focus box, landscape falling back to fanart plus clearlogo. A grouplist child is one 268px pitch,
which is Home's 243px art + 25px gutter, with `itemgap` 0. The viewport is exactly four pitches.
`GUIControlGroupList` scrolls a focused child to a viewport edge, so a whole number of pitches always
stops on a row boundary; any other height leaves a sliced row after the first scroll. Cards start at y16 and
end at y1063.

**Whole library (1.12.65).** Each row holds every title in its genre. `limit="5000"` on `<content>` is the provider's own ceiling, and Kodi applies the attribute after the plugin returns, so leaving a small value there would quietly re-cap the row. Provider 1.8.7 owns the index format and the first-row ordering.

**Up and Down (1.12.66).** Rows aimed `<onup>` and `<ondown>` at grouplist 8100 from the first hub until 1.12.65, and that left focus on the same row: `CGUIControlGroup` answers a focus request with its last focused child. Removing the actions does not work either, because the list sits inside a group, and only the grouplist's direct children get its navigation. Each list now names the neighbouring row group (8201-8214). A hidden group passes the move on through `CGUIWindow::OnMove`. The grouplist's `noop` actions stop a sparse page wrapping, because Kodi wraps a grouplist that has no up or down action. `validate_cinema.py` requires this wiring, and the lane presses real keys, because its old `SetFocus` calls could not see the fault.

**Focus column.** Up and Down already keep the column, so these rows need no column logic. `CGUIFixedListContainer::SelectItem` holds the cursor at `focusposition` (slot 0, x=80) and scrolls the row, and only the last three items move the cursor. `Control.Move` also goes through `SelectItem`, so it would scroll a row instead of moving its focus. The same rule means focus reaches the fourth slot, under the title card, only at the end of a row.

**Row titles.** They copy `Widget_Inline_Title`: rotated -90°, line centred on x=40, reading down from the
card top. The title's pre-rotation rect must stay inside the grouplist's clip (see "Titles" under 1.12.0), so
each child reserves 20px above its card and the label's top is 0. The focused row's title is full white, and
the others rest at 70%, Home's title strength.

**Title card.** It draws last, so it stays fixed over the rows. It uses the toasts' `rix_cinema_surface` and
`common/box.png`. Only a button's background follows its label's width, so the card is a disabled auto-width
button in a right-aligned grouplist, and a second one behind it (same label, transparent text, 40px larger
each way) carries `shadows/shadow-40.png`, because `bordertexture` is image-only. It covers a corner of the
fourth card in the top row, a deliberate cost: reserving a header strip would lose a third of the fourth row.

**Fade.** The rows' stale-category fade now takes 200 ms, so a page's rows arrive with a soft fade instead of
popping in. `start="100"` still matters: `time` does not change where the fade rests when its condition clears.

## Category hub memory (1.12.62, 1.12.63)

The hub window is `KEEP_IN_MEMORY`, and closing it does not free its rows' poster textures:
`CGUIWindow::FreeResources` calls `CGUIControlGroup::FreeResources()` with `immediately` false, and
`CGUIBaseContainer` then keeps its items. Each category therefore stacked on the last.
`Custom_1101_Hub.xml` carries one no-op conditional include per category key. A changed include
condition makes `CGUIWindow::NeedLoad` reload the window, so opening a different category frees the
old page first. A new category key needs a line there; `validate_cinema.py` holds the ten.

**Back frees the page (1.12.63).** A reload happens only when the window is activated, and the
`ActivateWindow` builtin ignores the window already open (`GUIBuiltins.cpp`), so `ReplaceWindow(1101)`
from the hub does nothing. `rixflix_category_return` therefore clears `RixFlix.Category`, then
activates `1110` (`Custom_1110_HubRelease.xml`, no controls), `1101` and Home. The rows' include is
conditional on a set category, so that activation loads an empty window and destroys the rows. All
of it runs in one call stack with no frame between, because none of these windows has a close
animation; adding one would make it visible. Series Back keeps the category and the page.

Other exits keep the page until the next tile: Kodi's Home action, which skips the timer, and
playback started from a row, which must return to a live hub. Deleted rows cancel their directory
jobs without waiting, so Back during a load is safe; a provider script already running finishes on
its own.

## 1.12.67: a separate Home quality row

Rick requested source details below the existing date, rating and runtime line.
Info_Panel now shows the resident service’s RixFlix.Quality property in a separate
two-line, 26px text box. Its identity must match the displayed movie, show or episode,
so a delayed response cannot show another card’s technical details.
The row disappears when facts are unavailable. It adds no artwork, timer or scrolling.
The Rixflix context service owns resolution, HDR profile, main audio and average
overall bitrate. For a series it explicitly describes the next episode.

The first live install exposed that Kodi conditions cannot concatenate $INFO tokens
as String.IsEqual’s second operand. Version 1.12.68 compares QualityType and
QualityDBID separately with the container’s native DBTYPE and DBID labels.


## 1.12.70: stable source details and category artwork

The Info dialog owns an opaque #080808 full-screen surface, above every custom
category window. The shared Info_Panel draws source facts only on its details
layer; the title-only layer no longer creates the duplicate quality row.
A 64px group reserves quality space for movies, series and episodes before the
worker replies. Its inner text still requires exact type/id agreement.
The editorial line uses 36px in Info_Panel, preserving 140 + 36 + 64 + 120 + 60
= 420px for title, editorial metadata, quality, plot and end time. Other Info_Line
callers retain their 80px spacing. Info details start at 440px, below the panel.

Categories use ten generated local JPEGs at extras/categories/{key}.jpg, shown as
560×315 cards with 16px gutters. Native labels and category keys remain available
to navigation and accessibility. Two movement slots keep the last card within
1920px. The provider owns the art paths. Decoded artwork is limited to the display
size; no external image URL or generated text control is required.


## 1.12.71: branded category states

Home Categories (507) shows the existing boot splash while focused. The live
visibility group (8070) sits above normal backgrounds and below Home content.
The full-size artwork is lifted 160px so its wordmark clears the 560×315 cards;
its lower edge rests behind the cards. No background download or generated asset
is added. Leaving Categories restores the normal media background immediately.

The category manifest's existing pending condition now shows the pause-screen
rixflix-wordmark.png (8988), centered in a 600×160 box. Native sine fade pulses
45–100% brightness in 900ms each direction. It stays recognizable at the dim end
and disappears when the manifest is ready. The empty-category explanation and
all directory/focus/row-ready conditions keep their existing behavior. Kodi
4665ec22 VisibleEffect.cpp confirms pulse auto-reverses Conditional animations.


## 1.12.72: white card focus bloom

The selected poster, landscape (including Premiere) and category layouts opt in
to Object_SelectBox's card_glow layer. The existing crisp focus line remains on
top. A small static white alpha texture adds exterior bloom and a short interior
falloff, with a single 180ms focus fade. It does not loop, scale the cards or
change dimensions, navigation or row spacing. Text-only selection boxes retain
their existing treatment.

The texture is generated from rounded-rectangle distance in
scripts/render_card_glow.py: 128×128 RGBA, 26px nine-slice corners, 64 KiB decoded.
It extends 6px past the card, fitting Home's 6px top inset and each 16px gutter.
The sharp border already extends 3px, so the extra outer bloom occupies only the
remaining inset. Its center is transparent; it cannot whitewash the poster.
The halo draws after the dark shadow and before the crisp outline, preventing
the shadow from dulling the white glow. White is explicit, independent of accent
color. No new artwork fetch, Python service or per-frame blur is added.


### 1.12.73: main-video seek previews

DialogSeekBar displays a prepared 320px main-video thumbnail above the timeline
while Player.Seeking. Native hh/mm/ss labels and six second-range conditions
choose ten-second buckets; there are no script calls or network reads per seek.
The identity-bound ready prefix is published by the Rixflix image worker. Empty
prefix preserves the existing bar. special://temp paths use Kodi cached-image
semantics, avoiding duplicate TextureCache entries. The white bloom and border
match the selected-card treatment; the target timestamp stays readable below
the frame. Real generation, active-item binding and native pixel proof belong
to Rixflix docs/home-theater.md; source validation alone is not native proof.

## 1.13.0: Search's Request row

Rick (2026-11-10): Search should also show Seerr-side titles in a row titled
"Request" under the results. OK requests the title, a held OK opens the usual
Info page, and a requested poster carries a chip.

**Row.** `Search_Request_Row` (Includes_Search.xml) is list **540** in group 541,
built from `List_Request_Row` / `Layout_Request`: the Results row's landscape card
plus a crimson chip and the same explicit white focus outline. Its content is
`$VAR[Path_RequestSearch]`: provider mode `request_search`, with `rev` and `q` as
refresh tokens. The provider reads the typed text from `RixFlix.SearchText`,
exactly as the live Results row does. The target is static and the order is
`playlist`, as for every provider row.

**Position.** The row shares the Results geometry (list top 510). A conditional
slide holds it 380 px lower, so the header and the top of the cards peek from the
bottom edge under Results. `Exp_RixFlix_Request_Raised` removes the slide while
the row has focus, or when the completed search found nothing in the library.
It never rises while results still load, so the row does not bounce per letter.
With focus on 540, groups 500 and 600 fade out, the info panel follows 540, and
the "No Results" labels and the item-count footer are hidden.

**Navigation.** Down from Results runs the unchanged `SetFocus($PARAM[id])` and
then, when `Exp_RixFlix_Request_Ready`, `SetFocus(540)`. Rixflix's search bench
reads the first action by its exact `Window.IsActive(11105)` condition, so keep
it first and unchanged. Down on 540 keeps the row; Up returns to 502, or to the
field when Results is empty; Back goes Home through 7900. Down from the field
goes to 540 when the library has nothing but the Request row is ready, and the
held-Down timer lands there in the same case.

**Click and Info.** `<onclick>` is `RunPlugin` on the item's own path (provider
mode `request`). An explicit onclick replaces the list provider's default action,
so nothing can play or browse the item. The items carry a movie/tvshow media type
and no database id: the held-OK route opens DialogVideoInfo for them unchanged.
There, `Action_DialogInfo_PlayMedia` and `Label_DialogInfo_PlayButton` test
`RixFlix.RequestKey` first: the button reads "Request" (or the chip text) and
runs the same request. Control 8000 skips `SendClick(8)` for these items.

**Chip.** The provider sets `RixFlix.RequestChip` ("Requested", "In library").
After a request it changes `RixFlix.RequestRev`; the content path changes, the
row reloads, and Kodi restores the selection by item path, so focus stays on the
poster that now carries the chip.

**Upkeep.** The window's `<onload>` runs provider mode `request_open` off the
GUI thread. It refreshes request state and advances the title index when due.

Source checks: `scripts/validate_cinema.py` PASS, including the row's static
target, single RunPlugin click, navigation targets and the unchanged 11105 Down.
The layout was written without a render; native placement, focus and the chip
need appliance proof, recorded in Rixflix `docs/home-theater.md`.

### 1.14.1 — cold foreground trailer deadline

The theater's Paper Tiger trailer timed out twice at the old 15-second
extraction deadline. An extraction-only comparison on November 11 resolved
it successfully in 18.69 seconds (176 formats); the first upcoming series
took 7.95 seconds and the previously played control took 7.64 seconds.
All three are public official trailers. The cold foreground fallback now
allows 30 seconds. Cached MP4 playback bypasses extraction. Cancellation,
exact player ownership and the separate 20-second playback-start deadline
remain in place. The diagnostic receipt is recorded in Rixflix's theater doc.

### 1.14.2 — stage rows get their content

1.14.0 and 1.14.1 shipped category pages and Coming Soon with empty rows. The first native
deploy (theater, 2026-11-11 02:09) failed its category smoke on the first page: focus stayed
on the hidden loading button `8901`, and Kodi logged no error.

Cause: `RixFlix_Stage_Row` passed the caller's `<content>` on through a `<nested />` placed
inside its `List_Premiere_Row` include. Kodi's `CGUIIncludes::InsertNested` fills
`<nested />` only when it is a definition's top node or a direct child of one. One level
deeper, the caller's children are dropped silently. Every row list had no `<content>`, stayed
empty and could not take focus. The other 126 `<nested />` uses in the skin are all direct.

Fix: the row is now two includes. `RixFlix_Stage_Row` is the group and label with a direct
`<nested />`. `RixFlix_Stage_List` has the `List_Premiere_Row` include as its definition's top
node, so its `<nested />` is direct too. A caller writes the list inside the row and gives it
`<content>` (and `<onclick>` on Coming Soon). Ids, navigation and geometry are unchanged.

`scripts/validate_cinema.py` gains `check_nested_depth()`: it fails on any include in `1080i/`
whose `<nested />` is deeper than Kodi fills. It fails on the 1.14.1 file and passes on this one.
The 1.14.0 source checks could not see this: they checked that the element existed, not where.

### 1.14.5 — Coming Soon Back names Home

The first native Coming Soon proof on 1.14.2 (theater, 2026-11-11 03:02) passed both trailer
paths and then failed its last step: `Input.Back` on the page opened Search, not Home. The page
used `PreviousMenu`, which follows Kodi's window history. Search is opened from Home with
`ReplaceWindow(1105)`, so Search can sit in that history where Home is expected. Why Home was
missing from the stack after two fullscreen trailers is not established; the proof now records
the window ids around Back so the next run shows it.

The page no longer depends on the history: the row stack and all four lists use
`ActivateWindow(Home)` for Back. Coming Soon is reached only from Home's tile, and a category
page already returns to Home by name (button `8900`). `validate_cinema.py` asserts it.
Not yet seen on the box.

### 1.14.6 — "Ends at" needs a runtime

The 03:02 Coming Soon frame showed "Ends at 3:02 AM" for the unreleased series 12 12 12. The
title has no runtime, and Kodi then computes `EndTimeResume` / `FinishTime` as the current
time, so the label was the clock. Both end-time lines in the shared `Info_Meta` panel
(`Includes_Info.xml`) now also require `Duration(secs)` above 0: the list item's for the
movie/episode line, the service item's for the override line. A title with a runtime is
unchanged. `validate_cinema.py` asserts both guards. Not yet seen on the box.

### 1.14.7: a Request title shows no file quality

The first Information page opened from a Search Request card (theater, 2026-11-11 03:22,
"Clayface") drew `1080p SDR · DD+ 5.1 · 7.3 Mbps`. The title is not in the library. The
quality line shows when `RixFlix.QualityType` and `RixFlix.QualityDBID` match the list item,
and a Request card has no DBID, so an empty `QualityDBID` matched it and the line kept the
last library title's text. The rule in `Info_Meta` (`Includes_Info.xml`) now also requires a
non-empty DBID and an empty `RixFlix.RequestKey`. Library titles are unchanged.
`validate_cinema.py` asserts both terms. Not yet seen on the box.

### 1.14.8 — Coming Soon Back is deferred; OK on a preview promotes by key

**Back.** 1.14.5 called `ActivateWindow(Home)` inside the page's `onback`. Native proof on
1.14.7 (theater, 2026-11-11 04:59, receipt `acceptance-9eDDBvIv`): Back reached Home, and 50 ms
later the window was Search with focus on 3000. A window switch inside `onback` lets Kodi apply
a second, default Back to the window it lands on; Home then followed its history, and Search
was in it. The same fact is already recorded on `rixflix_home_return` in `Timers.xml`. It also
explains the 03:02 result on `PreviousMenu`.

Back now uses the category page's route. The hidden button 8900 moved into the shared include
`RixFlix_Stage_Return`; both pages include it, and every Coming Soon `onback` is `8900`. Its
`onfocus` sets `RixFlix.CategoryReturn.Go`. The new timer `rixflix_coming_soon_return` (window
11138) clears the property and runs `ActivateWindow(Home)` after the key is consumed. The
category timer is unchanged: it also reloads the hub, which Coming Soon does not need.

**Promotion.** In one of four proof runs (04:56:55) OK on a card four seconds into its own
preview logged `ignored duplicate on-demand request (owner active)` and did nothing. The script
compared the click with `RixFlix.LocalTrailerMetadata`, which a skin timer sets; which side
differed was not logged. A Coming Soon preview is keyed `yt-<video id>` and the click names
that id, so the script now also promotes when the active key matches the click. The ignore line
now logs the active key and whether the hover property matched. The cause of the mismatch is
not established. Not yet seen on the box.

### 1.14.9 — Coming Soon reopens on its rows

1.14.8 passed its first native proof (`acceptance-EZ1FdfkW`: Back landed on Home's Categories
row, focus 507 at 0.14 s). The second visit failed (`acceptance-lxu6IFz3`, 05:46). The page
keeps its focus (`defaultcontrol always="false"`), and after a Back that focus was the hidden
button 8900. Opening the page again focused 8900, which armed the return and sent the viewer
straight back Home. The timer now runs `SetFocus(8810)` (the rows group) before
`ActivateWindow(Home)`, as the category timer parks on 8901. `validate_cinema.py` asserts the
order. Not yet seen on the box.

### 1.14.10: the Request chip has a wide pill for a stage and date

Rick asked for the Requested badge to carry an estimate (2026-11-11). The provider (1.9.4)
now sets the chip to where the request stands: "Searching", "Arriving now", "Coming in 9
days", "Theaters Dec 18", "Premieres Dec 5". Those run to 18 characters and "Requested" is 9.
A Kodi label cannot size its own background image, so `Layout_Request`
(`Includes_Layouts.xml`) draws one of two pills: 176 px as before, or 288 px when the
provider sets `RixFlix.RequestChipWide` (any chip over 10 characters). `validate_cinema.py`
asserts the two pills test that property in opposite senses. Not yet seen on the box.
