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


def min_confidence() -> float:
    return _addon.getSettingInt('min_confidence') / 100.0


def min_segment_seconds() -> float:
    return float(_addon.getSettingInt('min_segment_seconds'))


def intro_enabled() -> bool:
    return _addon.getSettingBool('enable_intro')


def recap_enabled() -> bool:
    return _addon.getSettingBool('enable_recap')


def debug_logging() -> bool:
    return _addon.getSettingBool('debug_log')


_VALID_BUTTON_THEMES = ('text', 'pill')


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
