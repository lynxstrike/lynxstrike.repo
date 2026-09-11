"""Visual "Button theme" preview/picker: two side-by-side panels, each an
actual live render of the Text and Pill themes -- Skip Intro and Skip Recap
stacked, using the real production textures and the current colour settings
for each segment kind independently. Not a static mockup: onInit() re-reads
every colour setting fresh each time this opens, so it always matches the
current choices.

Entered from Settings > Appearance's "Preview themes..." button via
RunScript(theme_picker.py) -- see theme_picker.py at the addon root -- so
this runs in its own short-lived interpreter process, separate from the
persistent service.py process, same reasoning as lib/color_picker.py.
"""

from __future__ import annotations

from typing import Optional

import xbmc
import xbmcaddon
import xbmcgui

from lib import settings as addon_settings
from lib.sidecar import log

# Explicit id required: see lib/color_picker.py's module docstring/comment
# for why (RunScript() against a raw file path gives Kodi no addon context
# to infer from).
ADDON = xbmcaddon.Addon('service.scenepass')
ADDON_PATH = ADDON.getAddonInfo('path')

_ACTION_BACK = (10, 92)

CTRL_TEXT_PANEL = 411
CTRL_TEXT_INTRO_GLYPH = 412
CTRL_TEXT_RECAP_GLYPH = 413
CTRL_PILL_PANEL = 421
CTRL_PILL_INTRO_BG = 422
CTRL_PILL_INTRO_GLYPH = 423
CTRL_PILL_RECAP_BG = 424
CTRL_PILL_RECAP_GLYPH = 425
CTRL_FOCUS_RING = 490

# Local (group-relative) (left, top, width, height) for each panel's
# focusable backdrop, matching service.scenepass-ThemePicker.xml exactly --
# used to move the focus-ring overlay, same technique as
# lib/color_picker.py:_CONTROL_RECT.
_RING_MARGIN = 6
_PANEL_RECT = {
    CTRL_TEXT_PANEL: (60, 76, 380, 280),
    CTRL_PILL_PANEL: (460, 76, 380, 280),
}


class ThemePickerDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.confirmed = False
        self.result_theme: Optional[str] = None

    def _update_focus_ring(self) -> None:
        rect = _PANEL_RECT.get(self.getFocusId())
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

    def onInit(self) -> None:
        try:
            self.getControl(CTRL_TEXT_INTRO_GLYPH).setColorDiffuse(addon_settings.button_color('intro'))
            self.getControl(CTRL_TEXT_RECAP_GLYPH).setColorDiffuse(addon_settings.button_color('recap'))
            self.getControl(CTRL_PILL_INTRO_BG).setColorDiffuse(addon_settings.button_color('intro'))
            self.getControl(CTRL_PILL_INTRO_GLYPH).setColorDiffuse(addon_settings.pill_text_color('intro'))
            self.getControl(CTRL_PILL_RECAP_BG).setColorDiffuse(addon_settings.button_color('recap'))
            self.getControl(CTRL_PILL_RECAP_GLYPH).setColorDiffuse(addon_settings.pill_text_color('recap'))
        except RuntimeError as exc:
            log(f'Theme picker preview colour failed: {exc!r}', xbmc.LOGWARNING)

        current = addon_settings.button_theme()
        self.setFocusId(CTRL_PILL_PANEL if current == 'pill' else CTRL_TEXT_PANEL)
        self._update_focus_ring()

    def onClick(self, controlId: int) -> None:
        if controlId == CTRL_TEXT_PANEL:
            self.result_theme = 'text'
            self.confirmed = True
            self.close()
        elif controlId == CTRL_PILL_PANEL:
            self.result_theme = 'pill'
            self.confirmed = True
            self.close()

    def onAction(self, action: xbmcgui.Action) -> None:
        if action.getId() in _ACTION_BACK:
            self.close()
            return
        self._update_focus_ring()


def create_theme_picker() -> ThemePickerDialog:
    return ThemePickerDialog(
        'service.scenepass-ThemePicker.xml',
        ADDON_PATH,
        'default',
        '1080i',
    )


def show_theme_picker() -> None:
    dlg = create_theme_picker()
    dlg.doModal()
    if dlg.confirmed and dlg.result_theme:
        ADDON.setSetting('button_theme', dlg.result_theme)
        log(f'button_theme set to {dlg.result_theme} via theme picker')
    del dlg
