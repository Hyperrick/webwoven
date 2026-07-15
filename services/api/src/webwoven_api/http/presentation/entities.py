"""Entity wire presentation shared by HTTP response adapters."""

from pydantic import ValidationError

from webwoven_api.graph.contracts import Entity
from webwoven_api.http.contracts.common import EntityResponse, ImageAttributionResponse


def _image_attribution_response(raw: str | None) -> ImageAttributionResponse | None:
    if raw is None:
        return None
    try:
        return ImageAttributionResponse.model_validate_json(raw, strict=True)
    except (ValidationError, ValueError):
        # Attribution must be complete before it is exposed as trusted provenance.
        return None


def entity_response(entity: Entity) -> EntityResponse:
    attribution = _image_attribution_response(entity.image_attribution_json)
    return EntityResponse(
        qid=entity.id,
        label=entity.label,
        description=entity.description,
        category=entity.category,
        entity_type=entity.entity_type,
        image_path=entity.image_path if attribution is not None else None,
        image_attribution=attribution,
    )
