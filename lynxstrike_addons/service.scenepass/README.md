# ScenePass for Kodi

Skip TV intros and recaps using ScenePass `.sp.json` sidecars beside each video.
The service reads Intro/Recap start and end times; it does not scan video itself.

## Playback

Enable Intro and Recap independently, and choose a skip button or automatic
skipping for each. The minimum segment length defaults to 8 seconds. Confidence
scores do not filter sidecars. Optionally hide an untouched skip button after
1-60 seconds (10 by default); otherwise it stays for the segment's duration.

## Theme Manager

Open **Configure > Themes > Open Theme Manager**. Choose **ScenePass**,
**SceneCast** or **Madnox**, then use the branded submenu to choose a style.
The Intro and Recap previews open in the centre. Select a numbered corner
to preview placement there.
Choose **Apply** to save, or **Cancel/Back** to discard the whole preview,
including colour-picker edits. The colour editor opens on its own page:
**Use colour** returns to the preview, and **Cancel** keeps the previous colour.
Only **Apply** in Theme Manager saves it. Reset colours affects the current design.

- **ScenePass:** **Text**, **Classic**, and **Modern** are available with every skin.
  Classic offers Solid, Outlined, and Split rectangles. Modern offers Solid,
  Outlined, and Split round pills.
  Both pill themes have separate background and lettering colours.
- **SceneCast:** Aeon SceneCast collaboration. Choose Pill (five styles) or Text
  (two styles). Original gold designs use fixed gold/ivory; custom styles
  expose only the colours that change the selected design.
- **Madnox:** Aeon Madnox collaboration, with four numbered themes: fixed
  original artwork, coloured icon/text with glow, a Madnox-logo pill, and
  dimensional lettering coloured independently of the red/gold M emblem.
  Theme 5 contains the legacy Madnox-logo Pill and remains available with every skin.

Collaboration themes require an approved skin installed **and active**. The manager
explains locked themes. Playback checks the active skin again whenever a skip
button appears, and after a skin switch. If unavailable it uses default Text,
preserving your saved preference. SceneCast (internal ID `cinema`) approves the exact skin ID `skin.aeon.scenecast`;
Madnox approves `skin.aeon.madnox` (verified from the supplied skin manifest).

Legacy Pill settings retain the Madnox-logo style because that was the artwork
shown by the previous version. Your colours and corner are retained.
See [THEME-SPEC.md](THEME-SPEC.md) for collaboration and theme registration.

## Family Share

“Let ScenePass scanners ease off the drive while playing” defaults on. After
10 seconds of playback, a small heartbeat in an existing library `.scenepass`
folder tells ScenePass PCs to read that drive more gently. It is removed when
playback stops. Libraries without Family Share are not written to. Negative
folder lookups are cached for 10 minutes.

## Installation and support

Install ScenePass from the lynxstrike Kodi repository, under Services.
English (en_GB) is currently included. Report bugs in the repository's issues.
MIT licensed. Source code and artwork were produced with AI tools.
