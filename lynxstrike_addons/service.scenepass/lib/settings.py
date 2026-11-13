"""Addon settings accessors."""

from __future__ import annotations

import re

import xbmcaddon

# Explicit id required: this module is imported both by the service process
# (started via the xbmc.service extension point, where Kodi infers the addon
# id automatically) and by color_picker.py (started via RunScript() against a
# raw file path, where Kodi has no addon context to infer -- xbmcaddon.Addon()
# with no argument raises "No valid addon id could be obtained" there).
_addon = xbmcaddon.Addon('service.scenepass')


def auto_skip(kind: str) -> bool:
    return _addon.getSettingBool(f'auto_skip_{kind}')


def skip_button_timeout() -> int:
    """Seconds before an untouched Skip button hides itself (the segment then
    plays on, as if the user chose to keep it); 0 = "Hide skip button" is off,
    so the button stays until the segment ends."""
    try:
        if not _addon.getSettingBool('hide_skip_button'):
            return 0
        return max(1, _addon.getSettingInt('skip_button_timeout'))
    except (RuntimeError, TypeError, ValueError):
        return 0


def min_segment_seconds() -> float:
    return float(_addon.getSettingInt('min_segment_seconds'))


def intro_enabled() -> bool:
    return _addon.getSettingBool('enable_intro')


def recap_enabled() -> bool:
    return _addon.getSettingBool('enable_recap')


def debug_logging() -> bool:
    return _addon.getSettingBool('debug_log')


def announce_playback() -> bool:
    """Family Share: let ScenePass scanners on the PCs ease off this library's
    drive while it's playing here (lib/share_beat.py)."""
    return _addon.getSettingBool('announce_playback')


_VALID_BUTTON_THEMES = ('text', 'pill', 'cinema', 'madnox', 'madnox-collection')


def button_theme() -> str:
    """'text' (default, no pill background) or 'pill' (translucent pill
    background behind the same icon/text glyph) -- see
    lib/skip_overlay.py:_BAKED_ASSETS. Falls back to 'text' for anything else,
    same reasoning as button_color(): this is a plain settings list, but
    nothing stops a stale/bad value in the underlying store.
    """
    theme = (_addon.getSettingString('button_theme') or '').strip().lower()
    return theme if theme in _VALID_BUTTON_THEMES else 'text'


# Registry of every user-configurable colour: target key -> (setting id,
# default hex). Target keys are also the RunScript() argument color_picker.py
# receives (Settings > Appearance's "Choose colour..." buttons), and the
# <default> values here must match resources/settings.xml's <default> for the
# same setting id -- keep both in sync.
#
# '<kind>_accent': the whole glyph in Text theme; the pill background in Pill
# theme (see lib/skip_overlay.py). '<kind>_pill_text': the icon/label glyph
# drawn on top of the pill in Pill theme, independent of the accent colour;
# defaults to white, i.e. no added tint on top of the plain glyph art.
_COLOR_SETTINGS = {
    'intro_accent': ('intro_button_color', 'FFBF00'),
    'recap_accent': ('recap_button_color', '002DB2'),
    'intro_pill_text': ('intro_pill_text_color', 'FFFFFF'),
    'recap_pill_text': ('recap_pill_text_color', 'FFFFFF'),
}

_HEX_COLOR_RE = re.compile(r'^[0-9A-Fa-f]{6}$')


def get_color_hex(target: str) -> str:
    """Validated 6-digit hex (no alpha) for a _COLOR_SETTINGS entry.

    Falls back to that entry's default on anything missing or malformed --
    the colour picker dialog (lib/color_picker.py) always writes a valid
    6-digit hex, but the same setting is also a plain hand-editable text
    field in Settings > Appearance, which Kodi doesn't validate, and a
    malformed value here must never reach setColorDiffuse() and break
    rendering.
    """
    setting_id, default = _COLOR_SETTINGS[target]
    hexval = (_addon.getSettingString(setting_id) or '').strip().lstrip('#')
    return hexval.upper() if _HEX_COLOR_RE.match(hexval) else default


def set_color_hex(target: str, hexval: str) -> None:
    setting_id, _default = _COLOR_SETTINGS[target]
    _addon.setSetting(setting_id, hexval)


def button_color(kind: str) -> str:
    """Opaque AARRGGBB colordiffuse string for the given segment kind's
    accent colour (see _COLOR_SETTINGS's '<kind>_accent' doc above).
    """
    return f'FF{get_color_hex(f"{kind}_accent")}'


def pill_text_color(kind: str) -> str:
    """Opaque AARRGGBB colordiffuse string for the given segment kind's
    pill-text colour (see _COLOR_SETTINGS's '<kind>_pill_text' doc above).
    """
    return f'FF{get_color_hex(f"{kind}_pill_text")}'


def restore_default_button_colors() -> None:
    """Reset every registered colour (accent + pill-text, both segment
    kinds) to its default.

    Used by restore_colors.py, the RunScript() target behind Settings >
    Appearance's "Restore default colours" button.
    """
    for setting_id, default in _COLOR_SETTINGS.values():
        _addon.setSetting(setting_id, default)


# Skip button corner on screen, numbered as in Settings > Appearance's
# "Button position" (1 = bottom right, the original placement, then
# clockwise: 2 bottom left, 3 top left, 4 top right).
_VALID_BUTTON_POSITIONS = (1, 2, 3, 4)


def button_position() -> int:
    try:
        pos = _addon.getSettingInt('button_position')
    except (RuntimeError, TypeError, ValueError):
        return 1
    return pos if pos in _VALID_BUTTON_POSITIONS else 1


def appearance_config():
    """Snapshot for staged edits. Preserve the previous Pill's Madnox artwork."""
    theme = button_theme()
    legacy_pill = (theme == 'pill' and _addon.getSettingInt('theme_catalog_version') < 1) or theme == 'madnox'
    if theme == 'madnox':
        theme = 'pill'
    pill_variant = _addon.getSettingString('pill_style')
    fmt = _addon.getSettingString('cinema_format')
    pill_style = _addon.getSettingString('cinema_pill_style')
    text_style = _addon.getSettingString('cinema_text_style')
    from lib.theme_registry import PILL_STYLES, TEXT_STYLES, MADNOX_STYLES, SCENEPASS_PILL_STYLES
    madnox_style = _addon.getSettingString('madnox_style')
    return {'theme': theme, 'position': button_position(),
            'madnox_style': madnox_style if madnox_style in {s[0] for s in MADNOX_STYLES} else 'theme-1',
            'pill_style': ('madnox' if legacy_pill else
                           pill_variant if pill_variant in {s[0] for s in SCENEPASS_PILL_STYLES} else 'classic'),
            'cinema_format': fmt if fmt in ('pill', 'text') else 'pill',
            'cinema_pill_style': pill_style if pill_style in {s[0] for s in PILL_STYLES} else 'original',
            'cinema_text_style': text_style if text_style in {s[0] for s in TEXT_STYLES} else 'original',
            'colors': {key: get_color_hex(key) for key in _COLOR_SETTINGS}}


def save_appearance(config):
    for key in ('button_theme', 'pill_style', 'cinema_format', 'cinema_pill_style', 'cinema_text_style', 'madnox_style'):
        _addon.setSetting(key, config['theme'] if key == 'button_theme' else config[key])
    _addon.setSettingInt('button_position', config['position'])
    for target, color in config['colors'].items():
        set_color_hex(target, color)
    _addon.setSettingInt('theme_catalog_version', 1)
