"""Tell ScenePass when this device is playing from a Family Share library.

ScenePass (the desktop app) limits how many scanners read a library's drive at
once; while a TV plays from that drive it drops to a single reader so playback
never stutters (ScenePass services/drive_load.py, Family Share Phase H).

While a video plays, this writes a small heartbeat file into the library's
communications folder and removes it when playback stops:

    <library root>/.scenepass/playing/<device>.beat

The library root is the nearest parent folder of the playing file that has a
``.scenepass`` folder -- which only exists when a ScenePass with Family Share
uses that library. No such folder: nothing is written, ever. ScenePass treats a
beat older than 90 s as finished, so a crashed or switched-off TV can't hold
the scanners back.
"""

from __future__ import annotations

import json
import time
from typing import Optional

import xbmc
import xbmcvfs

from lib.sidecar import log

SHARE_DIRNAME = '.scenepass'
BEAT_EVERY_SEC = 30.0
MAX_PARENT_LEVELS = 6


def _parent(path: str) -> Optional[str]:
    sep = '/' if '/' in path else '\\'
    trimmed = path.rstrip(sep)
    cut = trimmed.rfind(sep)
    if cut <= 0:
        return None
    return trimmed[:cut + 1]


def find_library_root(playing: str) -> Optional[str]:
    """Nearest parent (with trailing separator) holding a .scenepass folder."""
    if not playing or playing.startswith(('plugin://', 'http://', 'https://')):
        return None
    folder = _parent(playing)
    for _ in range(MAX_PARENT_LEVELS):
        if not folder:
            return None
        sep = '/' if '/' in folder else '\\'
        if xbmcvfs.exists(folder + SHARE_DIRNAME + sep):
            return folder
        folder = _parent(folder)
    return None


def _device_name() -> str:
    name = xbmc.getInfoLabel('System.FriendlyName') or 'Kodi'
    safe = ''.join(c if c.isalnum() or c in '-_ ' else '_' for c in name).strip()
    return (safe or 'Kodi')[:60]


class PlaybackBeat:
    def __init__(self) -> None:
        self._beat_path: Optional[str] = None
        self._playing: Optional[str] = None
        self._last = 0.0

    def tick(self, playing: str) -> None:
        """Call from the service loop while a video plays."""
        if playing != self._playing:
            self.stop()
            self._playing = playing
            root = find_library_root(playing)
            if root is None:
                return
            sep = '/' if '/' in root else '\\'
            folder = root + SHARE_DIRNAME + sep + 'playing' + sep
            if not xbmcvfs.exists(folder):
                xbmcvfs.mkdirs(folder)
            self._beat_path = folder + _device_name() + '.beat'
            self._last = 0.0
            log(f'Family Share playback beat: {self._beat_path}', xbmc.LOGINFO)
        if self._beat_path and time.time() - self._last >= BEAT_EVERY_SEC:
            self._write()

    def _write(self) -> None:
        body = json.dumps({'device': _device_name(), 'ts': time.time()})
        try:
            handle = xbmcvfs.File(self._beat_path, 'w')
            try:
                handle.write(body)
            finally:
                handle.close()
            self._last = time.time()
        except Exception as exc:              # a read-only share: just don't announce
            log(f'Family Share playback beat not written: {exc}', xbmc.LOGWARNING)
            self._beat_path = None

    def stop(self) -> None:
        """Playback ended / stopped / changed file: remove the beat at once."""
        if self._beat_path:
            try:
                xbmcvfs.delete(self._beat_path)
            except Exception:
                pass
        self._beat_path = None
        self._playing = None
        self._last = 0.0
