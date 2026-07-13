"""Public runtime configuration and health routes."""

from fastapi import APIRouter, Response, status

from webwoven_api.domain.scoring import Difficulty
from webwoven_api.http.contracts.system import ConfigResponse, HealthResponse
from webwoven_api.http.dependencies import ContainerDependency
from webwoven_api.sessions.models import SessionMode

router = APIRouter(tags=["system"])


@router.get("/api/v1/config", response_model=ConfigResponse)
async def get_config(container: ContainerDependency) -> ConfigResponse:
    categories = sorted({round_.category for round_ in container.graph.list_published_rounds()})
    return ConfigResponse(
        graph_version=container.graph.graph_version,
        categories=categories,
        difficulties=[difficulty.value for difficulty in Difficulty],
        modes=[SessionMode.SOLO.value, SessionMode.DAILY.value, SessionMode.RELAY.value],
    )


@router.get("/health/live", response_model=HealthResponse)
async def health_live() -> HealthResponse:
    return HealthResponse(status="ok", component="api")


@router.get("/health/ready", response_model=HealthResponse)
async def health_ready(
    response: Response,
    container: ContainerDependency,
) -> HealthResponse:
    healthy = container.graph.is_healthy() and await container.is_ready()
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if healthy else "degraded",
        component="api",
        graph_version=container.graph.graph_version,
    )


@router.get("/health/graph", response_model=HealthResponse)
async def health_graph(
    response: Response,
    container: ContainerDependency,
) -> HealthResponse:
    healthy = container.graph.is_healthy()
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if healthy else "degraded",
        component="graph",
        graph_version=container.graph.graph_version,
    )
