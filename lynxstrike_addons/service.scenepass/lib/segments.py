"""Parse intro/recap windows from a ScenePass .sp.json payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from lib import settings


@dataclass(frozen=True)
class Segment:
    kind: str
    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start

    def contains(self, position: float) -> bool:
        return self.start <= position < self.end


def _segment_from_block(kind: str, block: Any, min_duration: float) -> Optional[Segment]:
    if not isinstance(block, dict):
        return None
    try:
        start = float(block['start'])
        end = float(block['end'])
    except (KeyError, TypeError, ValueError):
        return None
    if start < 0 or end <= start or (end - start) < min_duration:
        return None
    return Segment(kind=kind, start=start, end=end)


def segments_from_payload(payload: dict[str, Any]) -> list[Segment]:
    min_duration = settings.min_segment_seconds()
    min_conf = settings.min_confidence()
    meta = payload.get('scenepass')
    confidence = 1.0
    if isinstance(meta, dict) and meta.get('confidence') is not None:
        try:
            confidence = float(meta['confidence'])
        except (TypeError, ValueError):
            confidence = 0.0
    if confidence < min_conf:
        return []

    found: list[Segment] = []
    if settings.recap_enabled():
        recap = _segment_from_block('recap', payload.get('recap'), min_duration)
        if recap:
            found.append(recap)
    if settings.intro_enabled():
        intro = _segment_from_block('intro', payload.get('intro'), min_duration)
        if intro:
            found.append(intro)
    found.sort(key=lambda seg: seg.start)
    return found


class PlaybackSegments:
    """Tracks which segments were handled during one play session."""

    def __init__(self, segments: Iterable[Segment]):
        self.segments = list(segments)
        self._handled: set[str] = set()

    def active_at(self, position: float) -> Optional[Segment]:
        for segment in self.segments:
            if segment.kind in self._handled:
                continue
            if segment.contains(position):
                return segment
        return None

    def mark_handled(self, kind: str) -> None:
        self._handled.add(kind)

    def reset_kind(self, kind: str) -> None:
        self._handled.discard(kind)

    def on_seek_before(self, position: float) -> None:
        for segment in self.segments:
            if position < segment.start:
                self.reset_kind(segment.kind)
