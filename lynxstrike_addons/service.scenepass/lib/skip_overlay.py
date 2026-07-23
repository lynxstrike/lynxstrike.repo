"""On-video Skip Intro / Skip Recap overlay (non-blocking)."""

from __future__ import annotations

from typing import Optional

import xbmcaddon
import xbmcgui

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo('path')

CTRL_GROUP = 100
CTRL_HIT = 101
CTRL_LABEL = 102
CTRL_ARROW = 103
CTRL_BG = 104

_ACTION_BACK = (10, 92)

# Layout tuned for 1080p reference coordinates.
PAD_LEFT = 14
PAD_RIGHT = 12
CHAR_W = 15
GAP_CHARS = 2
GAP_PX = 22   # exact half of original 45 px gap (3 * CHAR_W)
ARROW_W = 28
BTN_H = 52
MARGIN_RIGHT = 40
MARGIN_BOTTOM = 96
REF_WIDTH = 1920
REF_HEIGHT = 1080


def _button_labels() -> dict[str, str]:
    intro = ADDON.getLocalizedString(32011) or 'Skip Intro'
    recap = ADDON.getLocalizedString(32012) or 'Skip Recap'
    return {'intro': intro, 'recap': recap}


def _layout_width(label: str) -> tuple[int, int, int]:
    """Return (total_width, label_width, arrow_left)."""
    text_w = len(label) * CHAR_W
    arrow_left = PAD_LEFT + text_w + GAP_PX
    total = arrow_left + ARROW_W + PAD_RIGHT
    return total, text_w, arrow_left


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

    def _apply_layout(self, label: str) -> None:
        total_w, text_w, arrow_left = _layout_width(label)
        scale = self.getWidth() / REF_WIDTH if self.getWidth() else 1.0
        total_w = int(total_w * scale)
        text_w = int(text_w * scale)
        arrow_left = int(arrow_left * scale)
        arrow_w = int(ARROW_W * scale)
        btn_h = int(BTN_H * scale)
        pad_left = int(PAD_LEFT * scale)
        margin_right = int(MARGIN_RIGHT * scale)
        margin_bottom = int(MARGIN_BOTTOM * scale)

        screen_w = self.getWidth() or REF_WIDTH
        screen_h = self.getHeight() or REF_HEIGHT
        left = screen_w - total_w - margin_right
        top = screen_h - margin_bottom - btn_h

        group = self.getControl(CTRL_GROUP)
        group.setPosition(left, top)
        group.setWidth(total_w)
        group.setHeight(btn_h)

        bg = self.getControl(CTRL_BG)
        bg.setWidth(total_w)
        bg.setHeight(btn_h)

        lbl = self.getControl(CTRL_LABEL)
        lbl.setPosition(pad_left, 0)
        lbl.setWidth(text_w)
        lbl.setHeight(btn_h)
        lbl.setLabel(label)

        arrow = self.getControl(CTRL_ARROW)
        arrow.setPosition(arrow_left, int(10 * scale))
        arrow.setWidth(arrow_w)
        arrow.setHeight(arrow_w)

        hit = self.getControl(CTRL_HIT)
        hit.setWidth(total_w)
        hit.setHeight(btn_h)

    def onInit(self) -> None:
        self.is_open = True
        label = _button_labels().get(self.kind or '', 'Skip')
        try:
            self._apply_layout(label)
        except RuntimeError:
            try:
                self.getControl(CTRL_LABEL).setLabel(label)
            except RuntimeError:
                pass
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
