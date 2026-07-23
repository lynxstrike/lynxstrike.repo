"""Kodi player callbacks for ScenePass."""

from __future__ import annotations

from typing import Optional

import xbmc

from lib.segments import PlaybackSegments, segments_from_payload
from lib.sidecar import load_deploy_sidecar, log


class ScenePassPlayer(xbmc.Player):
    def __init__(self) -> None:
        super().__init__()
        self.playback_key: Optional[str] = None
        self.schedule: Optional[PlaybackSegments] = None

    def onAVStarted(self) -> None:
        self._load_schedule()

    def onPlayBackStopped(self) -> None:
        self._clear()

    def onPlayBackEnded(self) -> None:
        self._clear()

    def _clear(self) -> None:
        self.playback_key = None
        self.schedule = None

    def _load_schedule(self) -> None:
        self._clear()
        payload = load_deploy_sidecar(self)
        if payload is None:
            return
        segments = segments_from_payload(payload)
        if not segments:
            log('Sidecar loaded but no actionable segments', xbmc.LOGINFO)
            return
        folder, base = self._current_key_parts()
        if not folder or not base:
            return
        self.playback_key = folder + base
        self.schedule = PlaybackSegments(segments)
        kinds = ', '.join(f'{seg.kind} {seg.start:.1f}-{seg.end:.1f}s' for seg in segments)
        log(f'Schedule ready ({kinds})', xbmc.LOGINFO)

    def _current_key_parts(self) -> tuple[Optional[str], Optional[str]]:
        from lib.sidecar import playback_location
        return playback_location(self)
