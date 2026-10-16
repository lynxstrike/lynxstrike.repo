"""Custom colour picker dialog, shared by every colour setting this addon has
(the accent colour and, in Pill theme, the independent pill-text colour --
see lib/settings.py:_COLOR_SETTINGS for the full registry).

Kodi's native full colour picker (the `colorbutton` setting control) only
exists on Kodi 20 (Nexus) and newer, and this addon targets Nexus and older,
so this is a hand-built replacement laid out like a skin colour chooser:
a menu (OK / Custom hex / Default / Cancel), R/G/B sliders, a NOW | NEW
comparison bar, a grid of named swatches, and an info row naming the chosen
colour and the setting it applies to.

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
_ACTION_LEFT = 1
_ACTION_RIGHT = 2

CTRL_TITLE = 202
CTRL_NOW = 203
CTRL_NEW = 204
CTRL_NOW_LABEL = 205
CTRL_NEW_LABEL = 206
CTRL_INFO_SWATCH = 207
CTRL_INFO_NAME = 208
CTRL_INFO_HEX = 209
CTRL_INFO_TARGET = 210
CTRL_OK = 220
CTRL_CUSTOM = 221
CTRL_DEFAULT = 222
CTRL_CANCEL = 223
CTRL_FOCUS_RING = 290
CTRL_SELECT_RING = 291

# Slider rows: focus button id -> channel. Fill/nib/value controls are at
# +10/+20/+30 from the row id.
_SLIDERS = {240: 'r', 241: 'g', 242: 'b'}
_SLIDER_STEP = 5
_SLIDER_X, _SLIDER_Y, _SLIDER_STEP_Y, _SLIDER_W, _SLIDER_H = 30, 350, 52, 370, 44
_TRACK_X, _TRACK_W, _NIB_W = 16, 190, 12

# Named palette, in grid order (button ids 300+), matching
# service.scenepass-ColorPicker.xml's swatch colordiffuse values exactly.
_PALETTE_LIST = [
    ('Turquoise', '40E0D0'), ('Cyan', '00FFFF'), ('Pale Blue', 'AFEEEE'),
    ('Sky Blue', '87CEEB'), ('Deep Sky Blue', '00BFFF'), ('Royal Blue', '4169E1'),
    ('ScenePass Blue', '002DB2'), ('Teal', '008080'), ('Navy', '001F5B'),
    ('Mint', '98FB98'), ('Green', '00B22D'), ('Lime', '32CD32'),
    ('Chartreuse', '7FFF00'), ('Yellow Green', 'ADFF2F'), ('Lemon', 'FFF44F'),
    ('Khaki', 'F0E68C'), ('Gold', 'FFD700'), ('Amber', 'FFBF00'),
    ('Goldenrod', 'DAA520'), ('Orange', 'FFA500'), ('Dark Orange', 'FF8C00'),
    ('Orange Red', 'FF4500'), ('Red', 'FF0000'), ('Dark Red', 'B20000'),
    ('Crimson', 'DC143C'), ('Medium Purple', '9370DB'), ('Purple', '8000FF'),
    ('Magenta', 'FF00FF'), ('Hot Pink', 'FF69B4'), ('Light Pink', 'FFB6C1'),
    ('Lavender', 'E6E6FA'), ('Black', '000000'), ('Dark Grey', '404040'),
    ('Grey', '808080'), ('Silver', 'C0C0C0'), ('White', 'FFFFFF'),
]
_PALETTE = {300 + i: hexv for i, (_name, hexv) in enumerate(_PALETTE_LIST)}
_NAME_BY_HEX = {hexv: name for name, hexv in _PALETTE_LIST}
_GRID_COLS, _GRID_X, _GRID_Y, _CELL, _CELL_STEP = 9, 452, 124, 80, 92

# Group-relative (left, top, width, height) for every focusable control,
# used to move the focus ring without querying geometry back from Kodi.
_RING_MARGIN = 4
_CONTROL_RECT = {
    cid: (_GRID_X + (i % _GRID_COLS) * _CELL_STEP, _GRID_Y + (i // _GRID_COLS) * _CELL_STEP, _CELL, _CELL)
    for i, cid in enumerate(_PALETTE)
}
_CONTROL_RECT.update({cid: (30, 104 + k * 58, 370, 50)
                      for k, cid in enumerate((CTRL_OK, CTRL_CUSTOM, CTRL_DEFAULT, CTRL_CANCEL))})
_CONTROL_RECT.update({cid: (_SLIDER_X, _SLIDER_Y + k * _SLIDER_STEP_Y, _SLIDER_W, _SLIDER_H)
                      for k, cid in enumerate(_SLIDERS)})

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
        self._initial_hex = 'FFFFFF'
        self._rgb = {'r': 255, 'g': 255, 'b': 255}

    def configure(self, target: str, initial_hex: str) -> None:
        self.target = target
        self._set_from_hex(initial_hex)
        self._initial_hex = self._current_hex()

    def _set_from_hex(self, hexval: str) -> None:
        hexval = hexval.strip().lstrip('#')
        if _HEX_RE.match(hexval):
            self._rgb = {'r': int(hexval[0:2], 16), 'g': int(hexval[2:4], 16), 'b': int(hexval[4:6], 16)}

    def _current_hex(self) -> str:
        return '{r:02X}{g:02X}{b:02X}'.format(**self._rgb)

    def _refresh_controls(self) -> None:
        hexv = self._current_hex()
        try:
            self.getControl(CTRL_NEW).setColorDiffuse(f'FF{hexv}')
            self.getControl(CTRL_NEW_LABEL).setLabel(f'NEW  #{hexv}')
            self.getControl(CTRL_INFO_SWATCH).setColorDiffuse(f'FF{hexv}')
            self.getControl(CTRL_INFO_NAME).setLabel(_NAME_BY_HEX.get(hexv, 'Custom'))
            self.getControl(CTRL_INFO_HEX).setLabel(f'#{hexv}')
            for cid, channel in _SLIDERS.items():
                value = self._rgb[channel]
                fill_w = int(_TRACK_W * value / 255)
                self.getControl(cid + 10).setWidth(fill_w)
                nib_x = _SLIDER_X + _TRACK_X + fill_w - _NIB_W // 2
                self.getControl(cid + 20).setPosition(
                    max(_SLIDER_X + _TRACK_X, min(nib_x, _SLIDER_X + _TRACK_X + _TRACK_W - _NIB_W)),
                    _SLIDER_Y + list(_SLIDERS).index(cid) * _SLIDER_STEP_Y + 8)
                self.getControl(cid + 30).setLabel(str(value))
            self._update_select_ring(hexv)
        except RuntimeError as exc:
            log(f'Colour picker refresh failed: {exc!r}', xbmc.LOGWARNING)

    def _update_select_ring(self, hexv: str) -> None:
        ring = self.getControl(CTRL_SELECT_RING)
        cid = next((c for c, h in _PALETTE.items() if h == hexv), None)
        if cid is None:
            ring.setWidth(0)
            ring.setHeight(0)
            return
        x, y, w, h = _CONTROL_RECT[cid]
        ring.setPosition(x - 3, y - 3)
        ring.setWidth(w + 6)
        ring.setHeight(h + 6)

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
            self.getControl(CTRL_NOW).setColorDiffuse(f'FF{self._initial_hex}')
            self.getControl(CTRL_NOW_LABEL).setLabel(f'NOW  #{self._initial_hex}')
            setting_id = addon_settings._COLOR_SETTINGS.get(self.target, ('',))[0]
            self.getControl(CTRL_INFO_TARGET).setLabel(f'Saves to  |  {setting_id}')
        except RuntimeError as exc:
            log(f'Colour picker header failed: {exc!r}', xbmc.LOGWARNING)
        self._refresh_controls()
        # Start on the current colour's swatch when it's in the palette.
        cid = next((c for c, h in _PALETTE.items() if h == self._initial_hex), None)
        if cid is not None:
            self.setFocusId(cid)
        self._update_focus_ring()

    def onClick(self, controlId: int) -> None:
        if controlId == CTRL_OK:
            self.result_hex = self._current_hex()
            self.confirmed = True
            self.close()
        elif controlId == CTRL_CANCEL:
            self.close()
        elif controlId == CTRL_CUSTOM:
            self._on_hex_input()
        elif controlId == CTRL_DEFAULT:
            default = addon_settings._COLOR_SETTINGS.get(self.target, ('', 'FFFFFF'))[1]
            self._set_from_hex(default)
            self._refresh_controls()
        elif controlId in _SLIDERS:
            self._on_channel_input(controlId)
        elif controlId in _PALETTE:
            self._set_from_hex(_PALETTE[controlId])
            self._refresh_controls()
            # Picking a swatch is a complete, one-step colour choice -- jump
            # straight to OK so confirming is a single further press.
            self.setFocusId(CTRL_OK)
        self._update_focus_ring()

    def _on_hex_input(self) -> None:
        text = xbmcgui.Dialog().input('Hex colour (RRGGBB)', self._current_hex(),
                                      type=xbmcgui.INPUT_ALPHANUM)
        if text and _HEX_RE.match(text.strip().lstrip('#')):
            self._set_from_hex(text)
            self._refresh_controls()

    def _on_channel_input(self, controlId: int) -> None:
        channel = _SLIDERS[controlId]
        text = xbmcgui.Dialog().numeric(0, f'{channel.upper()} (0-255)', str(self._rgb[channel]))
        try:
            self._rgb[channel] = _clamp255(int(text))
        except (TypeError, ValueError):
            return
        self._refresh_controls()

    def onAction(self, action: xbmcgui.Action) -> None:
        action_id = action.getId()
        if action_id in _ACTION_BACK:
            self.close()
            return
        focus = self.getFocusId()
        # Slider rows point left/right at themselves in the XML, so focus
        # stays put and the press changes the value instead.
        if focus in _SLIDERS and action_id in (_ACTION_LEFT, _ACTION_RIGHT):
            channel = _SLIDERS[focus]
            delta = _SLIDER_STEP if action_id == _ACTION_RIGHT else -_SLIDER_STEP
            self._rgb[channel] = _clamp255(self._rgb[channel] + delta)
            self._refresh_controls()
        # Runs after Kodi has already moved focus for a directional press,
        # so getFocusId() reflects the new control.
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
