"""Persistence boundary owned by report intake."""

from typing import Protocol

from webwoven_api.reports.models import ContentReport


class ContentReportRepository(Protocol):
    async def create(self, report: ContentReport) -> None: ...
