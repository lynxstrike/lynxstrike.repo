"""On-video Skip Intro / Skip Recap overlay (non-blocking)."""

from __future__ import annotations

from typing import Optional

import xbmc
import xbmcaddon
import xbmcgui

from lib import settings
from lib.sidecar import log

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

_ACTION_BACK = (10, 92)

MARGIN_RIGHT = 40
MARGIN_BOTTOM = 96
REF_WIDTH = 1920
REF_HEIGHT = 1080

# Baked full-button art per theme (settings.button_theme()) and segment kind.
# Every texture here is a neutral white shape on transparent alpha (no
# baked-in hue) -- actual colour is applied at render time via
# setColorDiffuse(), never baked into the art itself.
#
# 'text' (default): control 106 alone, showing the icon+label glyph with no
# background, cropped almost tight to it (~94% solid content), tinted with
# the segment's accent colour (settings.button_color()). Control 107 (the
# pill-only glyph overlay, below) is unused and left fully transparent.
#
# 'pill': control 106 shows a translucent (~63% alpha) rounded-pill shape,
# tinted with the same accent colour as Text theme -- that's now "the pill
# colour". Control 107 draws the *exact same* icon+label glyph texture
# already used by Text theme on top of it, at the position/size given by
# 'glyph_rect_frac' (left, top, width, height, each a fraction of the pill's
# own on-screen size), independently tinted via
# settings.pill_text_color() (default white, i.e. no added tint at all).
#
# 'height_ref'/'aspect' size the button on screen exactly as before (a
# shared reference height per theme keeps intro/recap the same apparent
# size); 'glyph_rect_frac' locates control 107 within that same box, so it
# scales together with control 106 with no separate scale factor needed.
_BAKED_ASSETS = {
    'text': {
        'intro': {'texture': 'skip_intro_button.png', 'aspect': 5.26, 'height_ref': 50},
        'recap': {'texture': 'skip_recap_button.png', 'aspect': 5.70, 'height_ref': 50},
    },
    'pill': {
        'intro': {
            'texture': 'skip_intro_pill_bg.png', 'aspect': 3.8940, 'height_ref': 50,
            'glyph_texture': 'skip_intro_button.png',
            'glyph_rect_frac': (0.086015, 0.195181, 0.843441, 0.609639),
        },
        'recap': {
            'texture': 'skip_recap_pill_bg.png', 'aspect': 4.1333, 'height_ref': 50,
            'glyph_texture': 'skip_recap_button.png',
            'glyph_rect_frac': (0.081048, 0.195000, 0.852419, 0.610000),
        },
    },
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

    def _apply_layout(self, asset: dict, kind: str) -> None:
        scale = self.getWidth() / REF_WIDTH if self.getWidth() else 1.0
        btn_h = int(asset['height_ref'] * scale)
        btn_w = int(btn_h * asset['aspect'])
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
        baked.setImage(asset['texture'])
        baked.setPosition(0, 0)
        baked.setWidth(btn_w)
        baked.setHeight(btn_h)
        baked.setColorDiffuse(settings.button_color(kind))

        glyph = self.getControl(CTRL_GLYPH)
        glyph_rect_frac = asset.get('glyph_rect_frac')
        if glyph_rect_frac is not None:
            gx, gy, gw, gh = glyph_rect_frac
            glyph.setImage(asset['glyph_texture'])
            glyph.setPosition(int(btn_w * gx), int(btn_h * gy))
            glyph.setWidth(int(btn_w * gw))
            glyph.setHeight(int(btn_h * gh))
            glyph.setColorDiffuse(settings.pill_text_color(kind))
        else:
            # Text theme doesn't use this layer -- make sure it paints nothing
            # (it starts fully transparent per the XML anyway, but a previous
            # Pill-theme render could have left it visible/opaque here).
            glyph.setColorDiffuse('00FFFFFF')
            glyph.setWidth(0)
            glyph.setHeight(0)

        hit = self.getControl(CTRL_HIT)
        hit.setPosition(0, 0)
        hit.setWidth(btn_w)
        hit.setHeight(btn_h)

    def onInit(self) -> None:
        self.is_open = True
        kind = self.kind or ''
        theme_assets = _BAKED_ASSETS.get(settings.button_theme(), _BAKED_ASSETS['text'])
        asset = theme_assets.get(kind)
        if asset is None:
            log(f'No overlay art for segment kind {kind!r}', xbmc.LOGWARNING)
        else:
            try:
                self._apply_layout(asset, kind)
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
