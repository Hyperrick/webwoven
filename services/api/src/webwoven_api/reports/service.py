"""Content-report validation and creation."""

from datetime import UTC, datetime
from uuid import uuid4

from webwoven_api.domain.errors import DomainError
from webwoven_api.reports.models import ContentReport
from webwoven_api.reports.repository import ContentReportRepository


class ContentReportService:
    def __init__(self, repository: ContentReportRepository) -> None:
        self._repository = repository

    async def create(
        self,
        *,
        guest_id: str,
        entity_id: str | None,
        edge_id: str | None,
        round_id: str | None,
        reason: str,
        details: str,
    ) -> ContentReport:
        if entity_id is None and edge_id is None and round_id is None:
            raise DomainError(
                "report_subject_required",
                "Choose an entity, relationship, or round to report.",
            )
        normalized_details = details.strip()
        if not 5 <= len(normalized_details) <= 1000:
            raise DomainError(
                "invalid_report_details",
                "Report details must be 5–1000 characters after trimming.",
            )
        report = ContentReport(
            id=str(uuid4()),
            guest_id=guest_id,
            entity_id=entity_id,
            edge_id=edge_id,
            round_id=round_id,
            reason=reason,
            details=normalized_details,
            created_at=datetime.now(UTC),
        )
        await self._repository.create(report)
        return report
