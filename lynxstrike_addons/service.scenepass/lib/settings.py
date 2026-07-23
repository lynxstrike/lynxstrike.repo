"""Addon settings accessors."""

from __future__ import annotations

import xbmcaddon

_addon = xbmcaddon.Addon()


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
