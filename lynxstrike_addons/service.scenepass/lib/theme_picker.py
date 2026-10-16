"""Unified "Preview theme..." dialog: a miniature TV screen with the four
corner slots numbered as in Settings > Appearance's "Button position"
(1 bottom right, 2 bottom left, 3 top left, 4 top right). Every corner draws
the Skip Intro button in the chosen theme (Text/Pill) with the current
colours; the selected corner is full colour, the others dimmed. Not a static
mockup: onInit() re-reads every setting fresh each time this opens.

Text/Pill buttons under the screen switch the theme live; clicking a corner
saves theme + position and closes; Back/ESC closes without changing anything.

Entered via RunScript(theme_picker.py) -- see theme_picker.py at the addon
root -- so this runs in its own short-lived interpreter process, separate
from the persistent service.py process, same reasoning as lib/color_picker.py.
"""

from __future__ import annotations

import xbmc
import xbmcaddon
import xbmcgui

from lib import settings as addon_settings
from lib.sidecar import log
from lib.skip_overlay import _BAKED_ASSETS

# Explicit id required: see lib/color_picker.py's module docstring/comment
# for why (RunScript() against a raw file path gives Kodi no addon context
# to infer from).
ADDON = xbmcaddon.Addon('service.scenepass')
ADDON_PATH = ADDON.getAddonInfo('path')

_ACTION_BACK = (10, 92)

CTRL_SLOT_BASE = 510    # + position -> focusable corner slot
CTRL_GLYPH_BASE = 520   # + position -> icon/label glyph image
CTRL_NUMBER_BASE = 530  # + position -> corner number label
CTRL_PILL_BASE = 540    # + position -> pill background image
CTRL_TEXT_THEME = 561
CTRL_PILL_THEME = 562
CTRL_FOCUS_RING = 590

# Screen group's offset inside the dialog group, and each slot's
# (left, top, width, height) inside the screen group -- matching
# service.scenepass-ThemePicker.xml exactly.
_SCREEN_ORIGIN = (50, 76)
_SLOT_RECT = {
    1: (516, 350, 260, 76),
    2: (24, 350, 260, 76),
    3: (24, 24, 260, 76),
    4: (516, 24, 260, 76),
}
_THEME_RECT = {
    CTRL_TEXT_THEME: (240, 550, 200, 56),
    CTRL_PILL_THEME: (460, 550, 200, 56),
}
# Button drawing area inside a slot, right of the corner number.
_AREA_LEFT = 50
_AREA_RIGHT_PAD = 10
_BUTTON_HEIGHT = {'text': 36, 'pill': 46}
_RING_MARGIN = 6
_DIM_ALPHA = '40'


def _with_alpha(hex_argb: str, alpha: str) -> str:
    return alpha + hex_argb[-6:]


class ThemePickerDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.confirmed = False
        self.theme = 'text'
        self.position = 1

    def _focus_rect(self):
        focus = self.getFocusId()
        if focus in _THEME_RECT:
            return _THEME_RECT[focus]
        rect = _SLOT_RECT.get(focus - CTRL_SLOT_BASE)
        if rect is None:
            return None
        x, y, w, h = rect
        return (x + _SCREEN_ORIGIN[0], y + _SCREEN_ORIGIN[1], w, h)

    def _update_focus_ring(self) -> None:
        rect = self._focus_rect()
        if rect is None:
            return
        x, y, w, h = rect
        try:
            ring = self.getControl(CTRL_FOCUS_RING)
            ring.setPosition(x - _RING_MARGIN, y - _RING_MARGIN)
            ring.setWidth(w + 2 * _RING_MARGIN)
            ring.setHeight(h + 2 * _RING_MARGIN)
        except RuntimeError as exc:
            log(f'Theme picker focus ring failed: {exc!r}', xbmc.LOGWARNING)

    def _render(self) -> None:
        """Draw the Skip Intro button in every corner, in self.theme, the
        same layering as SkipOverlayDialog._apply_layout()."""
        asset = _BAKED_ASSETS[self.theme]['intro']
        accent = addon_settings.button_color('intro')
        pill_text = addon_settings.pill_text_color('intro')
        btn_h = _BUTTON_HEIGHT[self.theme]
        try:
            for pos, (sx, sy, sw, sh) in _SLOT_RECT.items():
                active = pos == self.position
                area_w = sw - _AREA_LEFT - _AREA_RIGHT_PAD
                btn_w = min(int(btn_h * asset['aspect']), area_w)
                left = sx + _AREA_LEFT + (area_w - btn_w) // 2
                top = sy + (sh - btn_h) // 2

                bg = self.getControl(CTRL_PILL_BASE + pos)
                glyph = self.getControl(CTRL_GLYPH_BASE + pos)
                frac = asset.get('glyph_rect_frac')
                if frac is not None:
                    gx, gy, gw, gh = frac
                    bg.setImage(asset['texture'])
                    bg.setPosition(left, top)
                    bg.setWidth(btn_w)
                    bg.setHeight(btn_h)
                    bg.setColorDiffuse(accent if active else _with_alpha(accent, _DIM_ALPHA))
                    glyph.setImage(asset['glyph_texture'])
                    glyph.setPosition(left + int(btn_w * gx), top + int(btn_h * gy))
                    glyph.setWidth(int(btn_w * gw))
                    glyph.setHeight(int(btn_h * gh))
                    glyph.setColorDiffuse(pill_text if active else _with_alpha(pill_text, _DIM_ALPHA))
                else:
                    bg.setColorDiffuse('00FFFFFF')
                    bg.setWidth(0)
                    bg.setHeight(0)
                    glyph.setImage(asset['texture'])
                    glyph.setPosition(left, top)
                    glyph.setWidth(btn_w)
                    glyph.setHeight(btn_h)
                    glyph.setColorDiffuse(accent if active else _with_alpha(accent, _DIM_ALPHA))

                self.getControl(CTRL_NUMBER_BASE + pos).setLabel(
                    str(pos), textColor='FFFFFFFF' if active else 'FFAAAAAA')

            for ctrl_id, theme in ((CTRL_TEXT_THEME, 'text'), (CTRL_PILL_THEME, 'pill')):
                chosen = theme == self.theme
                self.getControl(ctrl_id).setLabel(
                    ('✓ ' if chosen else '') + theme.capitalize(),
                    textColor='FFFFFFFF' if chosen else 'FFAAAAAA')
        except RuntimeError as exc:
            log(f'Theme picker preview failed: {exc!r}', xbmc.LOGWARNING)

    def onInit(self) -> None:
        self.theme = addon_settings.button_theme()
        self.position = addon_settings.button_position()
        self._render()
        self.setFocusId(CTRL_SLOT_BASE + self.position)
        self._update_focus_ring()

    def onClick(self, controlId: int) -> None:
        if controlId == CTRL_TEXT_THEME:
            self.theme = 'text'
            self._render()
        elif controlId == CTRL_PILL_THEME:
            self.theme = 'pill'
            self._render()
        elif controlId - CTRL_SLOT_BASE in _SLOT_RECT:
            self.position = controlId - CTRL_SLOT_BASE
            self.confirmed = True
            self.close()

    def onAction(self, action: xbmcgui.Action) -> None:
        if action.getId() in _ACTION_BACK:
            self.close()
            return
        self._update_focus_ring()


def show_theme_picker() -> None:
    dlg = ThemePickerDialog(
        'service.scenepass-ThemePicker.xml',
        ADDON_PATH,
        'default',
        '1080i',
    )
    dlg.doModal()
    if dlg.confirmed:
        ADDON.setSetting('button_theme', dlg.theme)
        ADDON.setSettingInt('button_position', dlg.position)
        log(f'button_theme={dlg.theme}, button_position={dlg.position} via preview')
    del dlg
