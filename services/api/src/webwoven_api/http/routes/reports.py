"""Content-report intake route."""

from fastapi import APIRouter, status

from webwoven_api.http.contracts.system import ContentReportRequest, ContentReportResponse
from webwoven_api.http.dependencies import ContainerDependency, GuestDependency

router = APIRouter(prefix="/api/v1/content-reports", tags=["content"])


@router.post("", response_model=ContentReportResponse, status_code=status.HTTP_201_CREATED)
async def create_content_report(
    body: ContentReportRequest,
    guest: GuestDependency,
    container: ContainerDependency,
) -> ContentReportResponse:
    report = await container.reports.create(
        guest_id=guest.id,
        entity_id=body.entity_qid,
        edge_id=body.edge_id,
        round_id=body.round_id,
        reason=body.reason,
        details=body.details,
    )
    return ContentReportResponse(id=report.id)
