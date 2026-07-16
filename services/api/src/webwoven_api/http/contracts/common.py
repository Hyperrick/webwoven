"""Shared API value objects with stable wire meaning."""

from typing import Literal, Self
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator, model_validator

_LICENSE_URLS = {
    "PUBLIC_DOMAIN": "https://creativecommons.org/publicdomain/mark/1.0",
    "CC0_1_0": "https://creativecommons.org/publicdomain/zero/1.0",
    "CC_BY_1_0": "https://creativecommons.org/licenses/by/1.0",
    "CC_BY_2_0": "https://creativecommons.org/licenses/by/2.0",
    "CC_BY_2_5": "https://creativecommons.org/licenses/by/2.5",
    "CC_BY_3_0": "https://creativecommons.org/licenses/by/3.0",
    "CC_BY_4_0": "https://creativecommons.org/licenses/by/4.0",
    "CC_BY_SA_1_0": "https://creativecommons.org/licenses/by-sa/1.0",
    "CC_BY_SA_2_0": "https://creativecommons.org/licenses/by-sa/2.0",
    "CC_BY_SA_2_5": "https://creativecommons.org/licenses/by-sa/2.5",
    "CC_BY_SA_3_0": "https://creativecommons.org/licenses/by-sa/3.0",
    "CC_BY_SA_4_0": "https://creativecommons.org/licenses/by-sa/4.0",
}
_WIKIMEDIA_THUMBNAIL_WIDTHS = {"480", "640"}

ImageLicenseId = Literal[
    "PUBLIC_DOMAIN",
    "CC0_1_0",
    "CC_BY_1_0",
    "CC_BY_2_0",
    "CC_BY_2_5",
    "CC_BY_3_0",
    "CC_BY_4_0",
    "CC_BY_SA_1_0",
    "CC_BY_SA_2_0",
    "CC_BY_SA_2_5",
    "CC_BY_SA_3_0",
    "CC_BY_SA_4_0",
]


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
    license_id: ImageLicenseId
    creator: str
    license_url: HttpUrl
    attribution_text: str
    context_label: str | None = None

    @model_validator(mode="after")
    def require_canonical_commons_provenance(self) -> Self:
        if any(
            not value.strip() for value in (self.file_name, self.creator, self.attribution_text)
        ):
            raise ValueError("image attribution text fields cannot be empty")
        if self.context_label is not None and not self.context_label.strip():
            raise ValueError("image context label cannot be empty")
        if self.creator.casefold() not in self.attribution_text.casefold():
            raise ValueError("image attribution text must identify the creator")
        if urlparse(str(self.original_url)).hostname != "upload.wikimedia.org":
            raise ValueError("original image must come from Wikimedia upload storage")
        if not _is_wikimedia_derivative(str(self.derivative_url)):
            raise ValueError("derivative image must come from an approved Wikimedia endpoint")
        if urlparse(str(self.source_url)).hostname != "commons.wikimedia.org":
            raise ValueError("image source must be Wikimedia Commons")
        if not _matches_license_url(str(self.license_url), self.license_id):
            raise ValueError("image license URL does not match its license identifier")
        return self


def _matches_license_url(value: str, license_id: ImageLicenseId) -> bool:
    actual = urlparse(value)
    expected = urlparse(_LICENSE_URLS[license_id])
    actual_path = actual.path.rstrip("/")
    expected_path = expected.path.rstrip("/")
    return (
        actual.scheme == "https"
        and actual.hostname == expected.hostname
        and (actual_path == expected_path or actual_path.startswith(f"{expected_path}/"))
        and not actual.query
        and not actual.fragment
    )


def _is_wikimedia_derivative(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme != "https":
        return False
    if parsed.hostname == "upload.wikimedia.org":
        return True
    query = parse_qs(parsed.query, strict_parsing=True)
    return (
        parsed.hostname == "commons.wikimedia.org"
        and parsed.path == "/w/thumb.php"
        and set(query) == {"f", "w"}
        and len(query["f"]) == 1
        and bool(query["f"][0].strip())
        and len(query["w"]) == 1
        and query["w"][0] in _WIKIMEDIA_THUMBNAIL_WIDTHS
    )


class EntityResponse(ApiModel):
    qid: str
    label: str
    description: str | None
    category: str
    entity_type: str
    image_path: str | None
    image_attribution: ImageAttributionResponse | None
    wikipedia_url: HttpUrl | None

    @field_validator("wikipedia_url")
    @classmethod
    def require_wikipedia_article(cls, value: HttpUrl | None) -> HttpUrl | None:
        if value is None:
            return None
        parsed = urlparse(str(value))
        host = parsed.hostname or ""
        if not (
            parsed.scheme == "https"
            and host.endswith(".wikipedia.org")
            and bool(host.removesuffix(".wikipedia.org"))
            and parsed.path.startswith("/wiki/")
            and len(parsed.path) > len("/wiki/")
            and not parsed.query
            and not parsed.fragment
        ):
            raise ValueError("Wikipedia URL must identify a canonical article")
        return value
