"""Entity wire presentation shared by HTTP response adapters."""

from webwoven_api.graph.contracts import Entity
from webwoven_api.http.contracts.common import EntityResponse


def entity_response(entity: Entity) -> EntityResponse:
    return EntityResponse(
        qid=entity.id,
        label=entity.label,
        description=entity.description,
        category=entity.category,
        entity_type=entity.entity_type,
        image_path=entity.image_path,
    )
