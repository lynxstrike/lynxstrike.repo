"""Playback polling and skip decisions."""

from __future__ import annotations

from typing import Optional

import xbmc

from lib import settings
from lib.player_hook import ScenePassPlayer
from lib.segments import Segment
from lib.sidecar import log
from lib.skip_overlay import SkipOverlayDialog, create_overlay


class SkipEngine:
    POLL_SECONDS = 0.35

    def __init__(self) -> None:
        self.monitor = xbmc.Monitor()
        self.player = ScenePassPlayer()
        self._overlay: Optional[SkipOverlayDialog] = None
        self._overlay_kind: Optional[str] = None
        self._last_position = 0.0
        self._last_playback_key: Optional[str] = None

    def run(self) -> None:
        log('Service started', xbmc.LOGINFO)
        while not self.monitor.abortRequested():
            if self.monitor.waitForAbort(self.POLL_SECONDS):
                break
            self._tick()
        self._close_overlay()
        log('Service stopped', xbmc.LOGINFO)

    def _tick(self) -> None:
        if not self.player.isPlayingVideo():
            if self._overlay is not None:
                log('Playback stopped, closing overlay')
            self._close_overlay()
            self._last_playback_key = None
            self._last_position = 0.0
            return

        schedule = self.player.schedule
        playback_key = self.player.playback_key
        if schedule is None or playback_key is None:
            return

        if playback_key != self._last_playback_key:
            if self._overlay is not None:
                log(f'Playback key changed ({self._last_playback_key!r} -> '
                    f'{playback_key!r}), closing overlay')
            self._last_playback_key = playback_key
            self._last_position = 0.0
            self._close_overlay()

        try:
            position = self.player.getTime()
        except RuntimeError:
            return

        if position + 0.5 < self._last_position:
            schedule.on_seek_before(position)
        self._last_position = position

        if self._overlay is not None:
            self._tick_overlay(position, schedule)
            return

        segment = schedule.active_at(position)
        if segment is None:
            return

        if settings.auto_skip(segment.kind):
            self._seek_segment(segment, schedule)
            return

        self._show_overlay(segment)

    def _tick_overlay(self, position: float, schedule) -> None:
        overlay = self._overlay
        if overlay is None:
            return

        if not overlay.is_open:
            self._finish_overlay(overlay, schedule)
            return

        active = schedule.active_at(position)
        if active is None or active.kind != self._overlay_kind:
            log(f'Segment no longer active at {position:.2f}s '
                f'(overlay was for {self._overlay_kind!r}), closing overlay')
            overlay.close()

    def _finish_overlay(self, overlay: SkipOverlayDialog, schedule) -> None:
        kind = self._overlay_kind
        self._overlay = None
        self._overlay_kind = None
        if kind is None:
            return

        schedule.mark_handled(kind)
        if not overlay.confirmed:
            log(f'User kept {kind}', xbmc.LOGINFO)
            return

        segment = next((s for s in schedule.segments if s.kind == kind), None)
        if segment is None:
            return
        try:
            self.player.seekTime(segment.end)
        except RuntimeError as exc:
            schedule.reset_kind(kind)
            log(f'Seek failed for {kind}: {exc}', xbmc.LOGWARNING)
            return
        log(f'Skipped {kind} -> {segment.end:.2f}s', xbmc.LOGINFO)

    def _show_overlay(self, segment: Segment) -> None:
        if self._overlay is not None:
            return
        overlay = create_overlay()
        overlay.set_segment(segment.kind)
        overlay.show()
        self._overlay = overlay
        self._overlay_kind = segment.kind
        log(f'Showing skip button for {segment.kind}', xbmc.LOGINFO)

    def _close_overlay(self) -> None:
        if self._overlay is not None and self._overlay.is_open:
            self._overlay.close()
        self._overlay = None
        self._overlay_kind = None

    def _seek_segment(self, segment: Segment, schedule) -> None:
        log(f'Auto-skipping {segment.kind} -> {segment.end:.2f}s', xbmc.LOGINFO)
        try:
            self.player.seekTime(segment.end)
        except RuntimeError as exc:
            log(f'Seek failed for {segment.kind}: {exc}', xbmc.LOGWARNING)
            return
        schedule.mark_handled(segment.kind)


def run_service() -> None:
    SkipEngine().run()
