"""Full-page colour editor with spatial navigation and explicit confirmation.

The picker only returns a proposed colour. Theme Manager Apply persists it.
RGB rows open numeric entry; arrows always move between visible controls.
Native RGB/hex entry temporarily hides this page to avoid overlapping dialogs.
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

from lib.color_layout import (
    PALETTE_LIST as _PALETTE_LIST, PALETTE as _PALETTE,
    CONTROL_RECTS as _CONTROL_RECT, SLIDERS as _SLIDERS,
    SLIDER_X as _SLIDER_X, SLIDER_Y as _SLIDER_Y,
    SLIDER_STEP_Y as _SLIDER_STEP_Y, TRACK_X as _TRACK_X,
    TRACK_W as _TRACK_W, NIB_W as _NIB_W,
)
from lib.spatial_navigation import navigation_map
_NAME_BY_HEX = {value: name for name, value in _PALETTE_LIST}
_RING_MARGIN = 4

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
        self._input_open = False

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
            self.getControl(CTRL_NEW_LABEL).setLabel(f'#{hexv}')
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
                    _SLIDER_Y + list(_SLIDERS).index(cid) * _SLIDER_STEP_Y + 16)
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

    def _update_focus_ring(self, focus: int = 0) -> None:
        # setFocusId() is queued, so right after it getFocusId() still
        # returns the old control -- pass the new id explicitly then.
        rect = _CONTROL_RECT.get(focus or self.getFocusId())
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
            self.getControl(CTRL_TITLE).setLabel(getattr(self, 'title_override', _TARGET_TITLES.get(self.target, 'Choose colour')))
            self.getControl(CTRL_NOW).setColorDiffuse(f'FF{self._initial_hex}')
            self.getControl(CTRL_NOW_LABEL).setLabel(f'#{self._initial_hex}')
            self.getControl(CTRL_INFO_TARGET).setLabel(getattr(self, 'footer_override', 'Use colour to confirm, or Cancel to keep the current colour.'))
        except RuntimeError as exc:
            log(f'Colour picker header failed: {exc!r}', xbmc.LOGWARNING)
        self._refresh_controls()
        for cid, links in navigation_map(_CONTROL_RECT).items():
            self.getControl(cid).setNavigation(
                self.getControl(links['up']), self.getControl(links['down']),
                self.getControl(links['left']), self.getControl(links['right']))
        # Start on the current colour's swatch when it's in the palette.
        cid = next((c for c, h in _PALETTE.items() if h == self._initial_hex), CTRL_CUSTOM)
        self.setFocusId(cid)
        self._update_focus_ring(cid)

    def onClick(self, controlId: int) -> None:
        if self._input_open:
            return
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
            self._update_focus_ring(CTRL_OK)
            return
        self._update_focus_ring()

    def _ask(self, callback):
        focus = self.getFocusId()
        self._input_open = True
        self.getControl(200).setVisible(False)
        try:
            return callback()
        finally:
            self.getControl(200).setVisible(True)
            self._input_open = False
            self.setFocusId(focus)
            self._update_focus_ring(focus)

    def _on_hex_input(self) -> None:
        text = self._ask(lambda: xbmcgui.Dialog().input(
            'Hex colour (RRGGBB)', self._current_hex(), type=xbmcgui.INPUT_ALPHANUM))
        if text and _HEX_RE.match(text.strip().lstrip('#')):
            self._set_from_hex(text)
            self._refresh_controls()

    def _on_channel_input(self, controlId: int) -> None:
        channel = _SLIDERS[controlId]
        text = self._ask(lambda: xbmcgui.Dialog().numeric(
            0, f'{channel.upper()} (0-255)', str(self._rgb[channel])))
        try:
            self._rgb[channel] = _clamp255(int(text))
        except (TypeError, ValueError):
            return
        self._refresh_controls()

    def onAction(self, action: xbmcgui.Action) -> None:
        if self._input_open:
            return
        action_id = action.getId()
        if action_id in _ACTION_BACK:
            self.close()
            return
        self._update_focus_ring()

    def onFocus(self, controlId):
        if not self._input_open:
            self._update_focus_ring(controlId)



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
