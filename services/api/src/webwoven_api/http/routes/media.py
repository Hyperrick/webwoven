"""Public delivery of locally bundled, attributed graph media."""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from webwoven_api.http.dependencies import ContainerDependency

router = APIRouter(tags=["media"])


@router.get("/api/v1/media/{asset_name}", include_in_schema=False)
async def graph_media(asset_name: str, container: ContainerDependency) -> FileResponse:
    asset = container.media.get(asset_name)
    if asset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Media asset not found")
    return FileResponse(
        asset.path,
        media_type=asset.content_type,
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "ETag": f'"{asset.sha256}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
