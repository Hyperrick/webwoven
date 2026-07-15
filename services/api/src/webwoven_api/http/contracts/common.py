"""Shared API value objects with stable wire meaning."""

from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, HttpUrl, model_validator

_LICENSE_URLS = {
    "PUBLIC_DOMAIN": "https://creativecommons.org/publicdomain/mark/1.0",
    "CC0_1_0": "https://creativecommons.org/publicdomain/zero/1.0",
    "CC_BY_4_0": "https://creativecommons.org/licenses/by/4.0",
}


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorResponse(ApiModel):
    code: str
    message: str


class ImageAttributionResponse(ApiModel):
    """Complete attribution for a locally bundled Wikimedia Commons image."""

    model_config = ConfigDict(extra="forbid", strict=True)

    file_name: str
    original_url: HttpUrl
    derivative_url: HttpUrl
    source_url: HttpUrl
    license_id: Literal["PUBLIC_DOMAIN", "CC0_1_0", "CC_BY_4_0"]
    creator: str
    license_url: HttpUrl
    attribution_text: str

    @model_validator(mode="after")
    def require_canonical_commons_provenance(self) -> Self:
        if any(
            not value.strip() for value in (self.file_name, self.creator, self.attribution_text)
        ):
            raise ValueError("image attribution text fields cannot be empty")
        if self.creator.casefold() not in self.attribution_text.casefold():
            raise ValueError("image attribution text must identify the creator")
        if urlparse(str(self.original_url)).hostname != "upload.wikimedia.org":
            raise ValueError("original image must come from Wikimedia upload storage")
        if urlparse(str(self.derivative_url)).hostname != "upload.wikimedia.org":
            raise ValueError("derivative image must come from Wikimedia upload storage")
        if urlparse(str(self.source_url)).hostname != "commons.wikimedia.org":
            raise ValueError("image source must be Wikimedia Commons")
        if str(self.license_url).rstrip("/") != _LICENSE_URLS[self.license_id]:
            raise ValueError("image license URL does not match its license identifier")
        return self


class EntityResponse(ApiModel):
    qid: str
    label: str
    description: str | None
    category: str
    entity_type: str
    image_path: str | None
    image_attribution: ImageAttributionResponse | None
