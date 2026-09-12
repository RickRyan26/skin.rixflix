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
