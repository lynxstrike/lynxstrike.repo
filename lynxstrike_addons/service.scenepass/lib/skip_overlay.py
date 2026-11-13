"""On-video Skip Intro / Skip Recap overlay (non-blocking)."""

from __future__ import annotations

from typing import Optional

import xbmc
import xbmcaddon
import xbmcgui

from lib import settings
from lib.sidecar import log
from lib.theme_registry import asset_for, anchor
from lib.theme_access import effective_config, skin_context
from lib.theme_render import paint

# Explicit id for consistency with lib/color_picker.py (there, it's required:
# see that module's comment). Here it runs in the service process (started
# via the xbmc.service extension point) where a bare Addon() would also
# resolve fine, but there's no reason to rely on that inference either.
ADDON = xbmcaddon.Addon('service.scenepass')
ADDON_PATH = ADDON.getAddonInfo('path')

CTRL_GROUP = 100
CTRL_HIT = 101
CTRL_BAKED = 106
CTRL_GLYPH = 107
CTRL_LOGO = 108

_ACTION_BACK = (10, 92)

MARGIN_RIGHT = 40
MARGIN_BOTTOM = 96
REF_WIDTH = 1920
REF_HEIGHT = 1080

class SkipOverlayDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.kind: Optional[str] = None
        self.confirmed = False
        self.is_open = False
        self.rendered_skin = None
        self.rendered_theme = 'text'

    def set_segment(self, kind: str) -> None:
        self.kind = kind

    def close(self) -> None:
        self.is_open = False
        super().close()

    def _apply_layout(self, kind: str) -> None:
        config, reason = effective_config(settings.appearance_config())
        self.rendered_theme = config['theme']
        self.rendered_skin = skin_context()
        asset = asset_for(config, kind, playback=True)
        screen_w = self.getWidth() or REF_WIDTH
        screen_h = self.getHeight() or REF_HEIGHT
        scale = screen_w / REF_WIDTH
        left, top = anchor(asset, config['position'], screen_w, screen_h, scale)
        group = self.getControl(CTRL_GROUP)
        group.setPosition(round(left), round(top))
        group.setWidth(round(asset['width'] * scale))
        group.setHeight(round(asset['height'] * scale))
        paint(self, (CTRL_BAKED, CTRL_GLYPH, CTRL_LOGO), asset, 0, 0, scale, config['colors'])
        bx, by, bw, bh = asset['body']
        hit = self.getControl(CTRL_HIT)
        hit.setPosition(round(bx * scale), round(by * scale))
        hit.setWidth(round(bw * scale))
        hit.setHeight(round(bh * scale))
        if reason:
            log('Theme unavailable; using Text. ' + reason, xbmc.LOGINFO)

    def onInit(self) -> None:
        self.is_open = True
        kind = self.kind or ''
        if kind not in ('intro', 'recap'):
            log(f'No overlay art for segment kind {kind!r}', xbmc.LOGWARNING)
        else:
            try:
                self._apply_layout(kind)
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
