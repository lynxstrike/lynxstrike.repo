# ScenePass theme contract

## Theme families

- Text: public, refreshed UHD lettering/icon assets; whole glyph uses segment accent.
- ScenePass Classic: public, with Solid, Outlined and Split rectangular styles.
- ScenePass Modern: public, with Solid, Outlined and Split round pills.
  Both pill themes use the same independent pill and lettering colours.
- SceneCast (internal ID `cinema`): collaboration for `skin.aeon.scenecast`. Pill format has five styles (accent underline, lettering, icon, original gold, accent + icon); Text format has two (original gold, icon + glow).
- Madnox: collaboration for `skin.aeon.madnox`, stable family ID `madnox-collection`.
  Four styles `theme-1` through `theme-4`, saved as `madnox_style`.
- Madnox Theme 5 / Madnox logo (legacy): Madnox-only like Themes 1-4 (same skin check, via `access_theme()`), preserves the existing colour logo, pill mask and independent lettering layer. The manager still saves it as `pill` with `pill_style=madnox`.

Registry: `lib/theme_registry.py`. Add future partner themes with a stable ID,
credit, artwork, colour roles and exact approved skin manifest IDs. Never use
skin names or folder names as access credentials. `skin.skindev` is not an
approved SceneCast alias. Kitmaster is the current collaboration partner;
per-theme attribution belongs in the registry once assigned.

## Collaboration theme access

Collaboration access is always enforced for previews, Apply and playback.
Any saved value from the former testing toggle is ignored.

`lib/theme_access.py` reads Kodi's actual active skin via `xbmc.getSkinDir()`
and verifies its installed manifest ID with `xbmcaddon.Addon(active)`.
The manager displays locked themes but does not render their collaboration artwork
or allow Apply. Apply rechecks access, even if the skin changed after opening.
The playback overlay independently checks immediately before every render,
ignoring script arguments and saved values as evidence of eligibility.
The service detects skin changes while a button is already open and repaints
with the effective theme without marking the segment handled or seeking.

If access fails, effective theme is public Text. The saved theme preference,
colours and position remain intact so it works again when its skin is active.
This is local compatibility/branding enforcement within an open-source addon.

## Editing and migration

Theme Manager owns theme, SceneCast format/style, four shared colour settings,
and named corner position. Previews and the colour picker edit an in-memory
snapshot. Only Apply saves. Back and Cancel discard every staged change.
Only relevant colour controls are shown. Original SceneCast gold/ivory are fixed.
Reset colours affects only the current design's colour roles, not position.

Legacy `button_theme=pill` meant Madnox artwork. Until the manager first saves
`theme_catalog_version=1`, read it as `pill` with `pill_style=madnox`.
Modern Solid keeps the existing `pill_style=classic` value. The other Modern
styles use `round-outline` and `round-split`. The Classic rectangles
use `solid`, `outline` and `split` with the same `pill` theme ID.
All previous colour setting IDs and position numbers are retained.

## Artwork and layout

Imported approved PNG layers are byte-for-byte copies. Source-to-asset paths
and SHA-256 hashes are in `resources/theme-artwork.json`.
Reimport using `tools/import_theme_artwork.py --source PATH`, where PATH holds
ScenePass-Cinema and ScenePass-UHD. Do not generate new artwork from composites.

SceneCast uses separate fixed base (`FFFFFFFF`) and neutral-white tint layers.
Tint only the variable layer according to the selected style: accent or text.
Original style has an empty tint layer. Full canvases and transparent glow
padding are preserved. Before display scaling, Intro canvas is 359x114 with body
(16,16,327,82); Recap is 381x114 with body (16,16,349,82). Masters are 8x.

Public Text is 263x50 (Intro) or 285x50 (Recap). Public Pill adds 32 horizontal
and 16 vertical pixels around the glyph: 327x82 or 349x82. Madnox retains
396x82, lettering (40,16,210,50), colour logo (232,15,160,52). The logo's
original 1600x520 image is untinted; neutral masks use the user's colours.

The dimensions above describe source geometry in 1920x1080 reference pixels.
The registry applies an 85% display scale to every button's canvas, layers and
hit target in both previews and playback; at UHD the result doubles uniformly.
Screen margins are 40 horizontal and 96 vertical pixels, measured to the body,
not the glow canvas. The invisible hit target uses the same body rectangle.
Both previews and playback use `lib/theme_render.py` and registry geometry.
Manager examples open enlarged and centred. Choosing a numbered corner moves
both examples to it and reduces their scale uniformly.
Playback uses the reference geometry without this preview enlargement.

Rebuild manager XML with `tools/build_theme_manager.py`.
Rebuild the Classic and Modern pill variants with `tools/build_scenepass_pills.py`.
Run `tools/verify_theme_manager.py` for source/XML syntax, artwork provenance,
layer geometry, exact-ID access, fallback, migration, remote navigation and
staged Apply/Cancel checks. Kodi screenshots/playback are separate runtime QA.

## Madnox production collection

Theme 1 uses the supplied combined M/lettering artwork in fixed red and gold,
without an addon tint or additional glow. Theme 2 uses separate neutral text/icon
and soft glow layers with the segment accent; the full-colour M is a fixed base.
Theme 3 fixes the charcoal pill and complete Madnox logo, tinting only the bold
lettering with the segment text colour. Theme 4 uses neutral dimensional lettering
over the fixed complete M, also using the segment text colour. There is no pill
on Themes 1, 2 or 4. Theme 1 exposes no colour controls.

Masters use 8x reference resolution. Theme 1/4 canvases are 400x144, Theme 2
400x112 and Theme 3 400x88. Layer count never exceeds the existing three image
controls. Reimport with `tools/import_madnox_themes.py --source PATH`, where PATH
is the approved `Madnox-All-4-Production` directory. Asset hashes are stored in
`resources/theme-madnox.json`. Original sources, generated transparent extractions,
the reproducible native UI builder and actual-layer colour previews are delivered
alongside the pack. This collection does not remap the old `madnox` setting value;
that value continues to migrate to the legacy Pill design.

The exact Madnox skin manifest was verified at
`Kodi-22/addons/skin.aeon.madnox_Dev/addon.xml`; its ID is `skin.aeon.madnox`.
The released Madnox skin (Kittmaster) has ID `skin.madnox` (2026-11-14); both IDs are allowed.
Folder names grant no access. Manager and playback use the existing exact-ID
installed-and-active checks and retain the user's preference during fallback.

## Directional navigation

Every focusable control uses the same rectangle-based spatial navigation rule
in lib/spatial_navigation.py. Only visible, enabled controls participate.
An arrow targets a control fully beyond the corresponding edge. Controls in
the same row/column take priority, ordered by edge distance and leading-edge
alignment. Otherwise the closest diagonal control in that direction wins.
At the outermost top row, Up wraps to the bottom row; at the outermost
bottom row, Down wraps to the top row, preferring horizontal alignment.
Horizontal outer edges stay put. Right from the family list enters the visible
submenu, and Left from its leading edge returns to the selected family.
Down below the preview reaches footer controls.

The family list opens branded ScenePass, SceneCast and Madnox submenus.
SceneCast focus explains the required skin.
Madnox locks all five styles, including the legacy Theme 5, when the Madnox skin is not active.

## SceneCast under-button colour

The supplied composite reference shows a broad coloured footprint below the
button. The source PNG uses very low alpha in this area, so its RGB preview
and its appearance over Kodi's dark background differ. Version 0.01.44 preserves the source alpha gradient, applies a linear gain of
6 with alpha capped at 112/255, and draws the result BEHIND the original base
and tint layers. No nonzero-to-opaque threshold is used. This preserves the supplied footprint
without tinting the panel lettering or gold core. The imported files are
unchanged. tools/build_cinema_glow.py generates the underlays reproducibly;
resources/theme-glow.json records source/output hashes and mapping.

## Colour editor

The editor uses the same 1640x940 page and 140,70 origin as Theme Manager.
lib/color_layout.py supplies palette/geometry to the generator and runtime.
Build with tools/build_color_picker.py. All 43 controls use spatial navigation;
RGB rows open numeric entry rather than intercepting directional keys.
Current and New colours have separate swatches and hex labels. Use colour
returns a candidate to the manager; Cancel keeps the previous candidate.
Only Theme Manager Apply persists it. The manager is hidden/inert while the
editor is open. The editor is hidden during native numeric/hex entry, then
focus returns to its invoking field. All Cancel/Back paths preserve saved
settings. The editor does not display internal setting IDs.

## SceneCast Pill 5: Accent + icon

Stable ID `accent-icon`; source is ScenePass-Cinema-All-5-Production/
05-addon-accent-icon/masters. The neutral tint mask colours the icon,
underline and glow with the segment accent. Fixed ivory lettering and
charcoal panel use the base layer without tint. The existing under-button
visibility mapping uses its own mask derived from this style, preserving
its supplied footprint. The removed Pill `icon-glow` style is not restored
and still falls back to Original gold. Both Text styles are unchanged.

Regression guard: generated glows must contain multiple intermediate alpha
levels and must never exceed alpha 112. New soft-texture filenames prevent
Kodi from reusing cached solid masks.
