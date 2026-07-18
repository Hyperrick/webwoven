"""Coarse opponent-safe Live Relay progress projection."""

from webwoven_api.sessions.models import SessionStatus


def progress_band(distance: int | None, optimal_distance: int, status: SessionStatus) -> int:
    if status is SessionStatus.COMPLETED:
        return 4
    if distance is None:
        return 0
    ratio = distance / max(optimal_distance, 1)
    if ratio <= 0.34:
        return 3
    if ratio <= 0.67:
        return 2
    if ratio < 1:
        return 1
    return 0
