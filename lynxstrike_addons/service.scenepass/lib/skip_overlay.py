"""On-video Skip Intro / Skip Recap overlay (non-blocking)."""

from __future__ import annotations

from typing import Optional

import xbmc
import xbmcaddon
import xbmcgui

from lib.sidecar import log

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo('path')

CTRL_GROUP = 100
CTRL_HIT = 101
CTRL_BAKED = 106

_ACTION_BACK = (10, 92)

MARGIN_RIGHT = 40
MARGIN_BOTTOM = 96
REF_WIDTH = 1920
REF_HEIGHT = 1080

# Baked full-button art per segment kind: background, label, and icon all in
# one texture, no pill. Each entry is (texture filename, width/height aspect
# ratio, reference display height). Both are flat solid-color text/icon
# designs that crop almost tight to the glyphs (~94% solid content), so a
# shared reference height keeps them the same apparent size on screen.
_BAKED_ASSETS = {
    'intro': ('skip_intro_button.png', 5.26, 50),
    'recap': ('skip_recap_text.png', 5.70, 50),
}


class SkipOverlayDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.kind: Optional[str] = None
        self.confirmed = False
        self.is_open = False

    def set_segment(self, kind: str) -> None:
        self.kind = kind

    def close(self) -> None:
        self.is_open = False
        super().close()

    def _apply_layout(self, texture: str, aspect: float, height_ref: float) -> None:
        scale = self.getWidth() / REF_WIDTH if self.getWidth() else 1.0
        btn_h = int(height_ref * scale)
        btn_w = int(btn_h * aspect)
        margin_right = int(MARGIN_RIGHT * scale)
        margin_bottom = int(MARGIN_BOTTOM * scale)

        screen_w = self.getWidth() or REF_WIDTH
        screen_h = self.getHeight() or REF_HEIGHT
        left = screen_w - btn_w - margin_right
        top = screen_h - margin_bottom - btn_h

        group = self.getControl(CTRL_GROUP)
        group.setPosition(left, top)
        group.setWidth(btn_w)
        group.setHeight(btn_h)

        baked = self.getControl(CTRL_BAKED)
        baked.setImage(texture)
        baked.setPosition(0, 0)
        baked.setWidth(btn_w)
        baked.setHeight(btn_h)

        hit = self.getControl(CTRL_HIT)
        hit.setPosition(0, 0)
        hit.setWidth(btn_w)
        hit.setHeight(btn_h)

    def onInit(self) -> None:
        self.is_open = True
        kind = self.kind or ''
        asset = _BAKED_ASSETS.get(kind)
        if asset is None:
            log(f'No overlay art for segment kind {kind!r}', xbmc.LOGWARNING)
        else:
            try:
                self._apply_layout(*asset)
            except RuntimeError as exc:
                log(f'Overlay layout failed for kind {kind!r}: {exc!r}', xbmc.LOGWARNING)
        self.setFocusId(CTRL_HIT)

    def onClick(self, controlId: int) -> None:
        if controlId == CTRL_HIT:
            self.confirmed = True
            self.close()

    def onAction(self, action: xbmcgui.Action) -> None:
        if action.getId() in _ACTION_BACK:
            self.close()


def create_overlay() -> SkipOverlayDialog:
    return SkipOverlayDialog(
        'service.scenepass-SkipOverlay.xml',
        ADDON_PATH,
        'default',
        '1080i',
    )
