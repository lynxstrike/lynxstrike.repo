"""Custom hex/RGB colour picker dialog, shared by every colour setting this
addon has (the accent colour and, in Pill theme, the independent pill-text
colour -- see lib/settings.py:_COLOR_SETTINGS for the full registry).

Kodi's native full colour picker (the `colorbutton` setting control) only
exists on Kodi 20 (Nexus) and newer, and this addon targets Nexus and older,
so this is a hand-built replacement: a WindowXMLDialog with a hex field,
separate R/G/B number fields, a live preview swatch, and the 8 preset swatches
also offered in the plain settings list.

Entered from Settings > Appearance via RunScript(color_picker.py, <target>)
-- <target> a _COLOR_SETTINGS key -- see color_picker.py at the addon root,
so this runs in its own short-lived interpreter process, separate from the
persistent service.py process. That's fine: settings.get_color_hex()/
button_color()/pill_text_color() re-read the setting on every call rather
than caching, so the running service picks up a change on its next render.
"""

from __future__ import annotations

import re
from typing import Optional

import xbmc
import xbmcaddon
import xbmcgui

from lib import settings as addon_settings
from lib.sidecar import log

# Explicit id required here: this dialog is opened by color_picker.py via
# RunScript() against a raw file path, not through a declared extension
# point, so Kodi has no addon context to infer -- xbmcaddon.Addon() with no
# argument raises "No valid addon id could be obtained" in that case.
ADDON = xbmcaddon.Addon('service.scenepass')
ADDON_PATH = ADDON.getAddonInfo('path')

_ACTION_BACK = (10, 92)

CTRL_TITLE = 202
CTRL_PREVIEW = 203
CTRL_HEX = 205
CTRL_R = 207
CTRL_G = 209
CTRL_B = 211
CTRL_OK = 230
CTRL_CANCEL = 231
CTRL_FOCUS_RING = 290

# Local (group-relative) (left, top, width, height) for every focusable
# control, matching service.scenepass-ColorPicker.xml exactly -- used to move
# the focus-ring overlay (see _update_focus_ring) without needing to query
# control geometry back from Kodi at runtime.
_RING_MARGIN = 4
_CONTROL_RECT = {300 + i: (30 + (i % 8) * 68, 104 + (i // 8) * 68, 60, 60) for i in range(48)}
_CONTROL_RECT.update({
    CTRL_HEX: (610, 258, 260, 40),
    CTRL_R: (610, 346, 260, 40),
    CTRL_G: (610, 434, 260, 40),
    CTRL_B: (610, 522, 260, 40),
    CTRL_OK: (618, 610, 120, 50),
    CTRL_CANCEL: (750, 610, 120, 50),
})

# 48-swatch palette grid (control ids 300-347): an 8-hue x 6-row HSV spectrum
# (grayscale ramp + 5 saturation/value bands), matching the swatch colours
# baked into service.scenepass-ColorPicker.xml's colordiffuse attributes.
_PALETTE = {
    300: '000000', 301: '242424', 302: '494949', 303: '6D6D6D',
    304: '929292', 305: 'B6B6B6', 306: 'DBDBDB', 307: 'FFFFFF',
    308: 'FF0000', 309: 'FFBF00', 310: '80FF00', 311: '00FF40',
    312: '00FFFF', 313: '0040FF', 314: '8000FF', 315: 'FF00BF',
    316: 'B20000', 317: 'B28600', 318: '59B200', 319: '00B22D',
    320: '00B2B2', 321: '002DB2', 322: '5900B2', 323: 'B20086',
    324: 'FF7373', 325: 'FFDC73', 326: 'B9FF73', 327: '73FF96',
    328: '73FFFF', 329: '7396FF', 330: 'B973FF', 331: 'FF73DC',
    332: '730000', 333: '735600', 334: '397300', 335: '00731D',
    336: '007373', 337: '001D73', 338: '390073', 339: '730056',
    340: 'F29D9D', 341: 'F2DD9D', 342: 'C8F29D', 343: '9DF2B3',
    344: '9DF2F2', 345: '9DB3F2', 346: 'C89DF2', 347: 'F29DDD',
}

_HEX_RE = re.compile(r'^[0-9A-Fa-f]{6}$')

_TARGET_TITLES = {
    'intro_accent': 'Skip Intro button colour',
    'recap_accent': 'Skip Recap button colour',
    'intro_pill_text': 'Skip Intro pill text colour',
    'recap_pill_text': 'Skip Recap pill text colour',
}


def _clamp255(value: int) -> int:
    return max(0, min(255, value))


class ColorPickerDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.target = 'intro_accent'
        self.confirmed = False
        self.result_hex: Optional[str] = None
        self._r = self._g = self._b = 255

    def configure(self, target: str, initial_hex: str) -> None:
        self.target = target
        self._set_from_hex(initial_hex)

    def _set_from_hex(self, hexval: str) -> None:
        hexval = hexval.strip().lstrip('#')
        if _HEX_RE.match(hexval):
            self._r = int(hexval[0:2], 16)
            self._g = int(hexval[2:4], 16)
            self._b = int(hexval[4:6], 16)

    def _current_hex(self) -> str:
        return f'{self._r:02X}{self._g:02X}{self._b:02X}'

    def _refresh_controls(self) -> None:
        try:
            self.getControl(CTRL_HEX).setLabel(self._current_hex())
            self.getControl(CTRL_R).setLabel(str(self._r))
            self.getControl(CTRL_G).setLabel(str(self._g))
            self.getControl(CTRL_B).setLabel(str(self._b))
            self.getControl(CTRL_PREVIEW).setColorDiffuse(f'FF{self._current_hex()}')
        except RuntimeError as exc:
            log(f'Colour picker refresh failed: {exc!r}', xbmc.LOGWARNING)

    def _update_focus_ring(self) -> None:
        rect = _CONTROL_RECT.get(self.getFocusId())
        if rect is None:
            return
        x, y, w, h = rect
        try:
            ring = self.getControl(CTRL_FOCUS_RING)
            ring.setPosition(x - _RING_MARGIN, y - _RING_MARGIN)
            ring.setWidth(w + 2 * _RING_MARGIN)
            ring.setHeight(h + 2 * _RING_MARGIN)
        except RuntimeError as exc:
            log(f'Colour picker focus ring failed: {exc!r}', xbmc.LOGWARNING)

    def onInit(self) -> None:
        try:
            self.getControl(CTRL_TITLE).setLabel(_TARGET_TITLES.get(self.target, 'Choose colour'))
        except RuntimeError as exc:
            log(f'Colour picker title failed: {exc!r}', xbmc.LOGWARNING)
        self._refresh_controls()
        # Initial focus comes from the XML's <defaultcontrol> (the top-left
        # grid swatch), not forced here, so it stays in one place to reason
        # about; getFocusId() already reflects that by the time onInit runs.
        self._update_focus_ring()

    def onClick(self, controlId: int) -> None:
        self._update_focus_ring()
        if controlId == CTRL_OK:
            self.result_hex = self._current_hex()
            self.confirmed = True
            self.close()
        elif controlId == CTRL_CANCEL:
            self.close()
        elif controlId == CTRL_HEX:
            self._on_hex_input()
        elif controlId in (CTRL_R, CTRL_G, CTRL_B):
            self._on_channel_input(controlId)
        elif controlId in _PALETTE:
            self._set_from_hex(_PALETTE[controlId])
            self._refresh_controls()
            # Picking a swatch is a complete, one-step colour choice (unlike
            # a hex/R/G/B edit, which is usually one step in fine-tuning) --
            # jump straight to OK so confirming is a single further press.
            self.setFocusId(CTRL_OK)
            self._update_focus_ring()

    def _on_hex_input(self) -> None:
        text = self.getControl(CTRL_HEX).getText()
        if _HEX_RE.match(text.strip().lstrip('#')):
            self._set_from_hex(text)
        self._refresh_controls()

    def _on_channel_input(self, controlId: int) -> None:
        text = self.getControl(controlId).getText()
        try:
            value = _clamp255(int(text))
        except ValueError:
            value = 0
        if controlId == CTRL_R:
            self._r = value
        elif controlId == CTRL_G:
            self._g = value
        else:
            self._b = value
        self._refresh_controls()

    def onAction(self, action: xbmcgui.Action) -> None:
        if action.getId() in _ACTION_BACK:
            self.close()
            return
        # Runs after Kodi's own default handling has already moved focus for
        # a directional press (same reasoning as the slider-tracking pattern
        # many Kodi addons use), so getFocusId() here reflects the new
        # control, not the one focus just left.
        self._update_focus_ring()


def create_picker() -> ColorPickerDialog:
    return ColorPickerDialog(
        'service.scenepass-ColorPicker.xml',
        ADDON_PATH,
        'default',
        '1080i',
    )


def show_color_picker(target: str) -> None:
    initial_hex = addon_settings.get_color_hex(target)
    dlg = create_picker()
    dlg.configure(target, initial_hex)
    dlg.doModal()
    if dlg.confirmed and dlg.result_hex:
        addon_settings.set_color_hex(target, dlg.result_hex)
        log(f'{target} colour set to {dlg.result_hex} via colour picker')
    del dlg
