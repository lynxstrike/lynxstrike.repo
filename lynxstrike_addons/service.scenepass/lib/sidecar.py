"""Load ScenePass deploy sidecars during Kodi playback."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import xbmc
import xbmcvfs

from lib.settings import debug_logging

ADDON_ID = 'service.scenepass'
SP_SUFFIX = '.sp.json'


def log(message: str, level=xbmc.LOGDEBUG) -> None:
    if level == xbmc.LOGDEBUG and not debug_logging():
        return
    xbmc.log(f'[{ADDON_ID}] {message}', level)


def playback_location(player) -> tuple[Optional[str], Optional[str]]:
    """Return (folder, basename-without-ext) for the active video, if known."""
    playing = ''
    try:
        playing = player.getPlayingFile() or ''
    except RuntimeError:
        playing = ''

    if playing and not playing.startswith('plugin://'):
        folder, filename = os.path.split(playing)
        base, _ = os.path.splitext(filename)
        if not folder:
            return None, None
        sep = '/' if '/' in folder else '\\'
        if not folder.endswith(sep):
            folder += sep
        return folder, base

    folder = xbmc.getInfoLabel('Player.Folderpath')
    filename = xbmc.getInfoLabel('Player.Filename')
    if not folder or not filename:
        return None, None
    base, _ = os.path.splitext(filename)
    return folder, base


def sidecar_path(player) -> Optional[str]:
    folder, base = playback_location(player)
    if not folder or not base:
        return None
    return folder + base + SP_SUFFIX


def load_deploy_sidecar(player) -> Optional[dict[str, Any]]:
    path = sidecar_path(player)
    if not path:
        log('Could not resolve playback path for sidecar lookup', xbmc.LOGINFO)
        return None
    if not xbmcvfs.exists(path):
        log(f'No sidecar: {path}')
        return None
    try:
        with xbmcvfs.File(path, 'r') as handle:
            payload = json.loads(handle.read())
    except (TypeError, ValueError, OSError) as exc:
        log(f'Invalid sidecar {path}: {exc}', xbmc.LOGWARNING)
        return None
    if not isinstance(payload, dict):
        log(f'Sidecar root must be an object: {path}', xbmc.LOGWARNING)
        return None
    log(f'Loaded sidecar: {path}')
    return payload
