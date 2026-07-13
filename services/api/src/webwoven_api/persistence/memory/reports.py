"""In-memory moderation report sink."""

import asyncio

from webwoven_api.reports.models import ContentReport


class MemoryContentReportRepository:
    def __init__(self) -> None:
        self._reports: list[ContentReport] = []
        self._lock = asyncio.Lock()

    async def create(self, report: ContentReport) -> None:
        async with self._lock:
            self._reports.append(report)

    async def all(self) -> tuple[ContentReport, ...]:
        async with self._lock:
            return tuple(self._reports)
