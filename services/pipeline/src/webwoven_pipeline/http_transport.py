from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib.request import Request, urlopen


class JsonTransport(Protocol):
    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
    ) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class BinaryResponse:
    body: bytes
    content_type: str
    final_url: str


class BinaryTransport(Protocol):
    def get_bytes(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
        max_bytes: int,
    ) -> BinaryResponse: ...


class UrllibJsonTransport:
    """Small standard-library transport used only by offline acquisition."""

    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
    ) -> dict[str, Any]:
        request = Request(url, headers=dict(headers))
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS callers
            value: object = json.load(response)
        if not isinstance(value, dict):
            raise ValueError("expected an object response")
        return cast(dict[str, Any], value)


class UrllibBinaryTransport:
    """Bounded binary transport used only by offline media acquisition."""

    def get_bytes(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
        max_bytes: int,
    ) -> BinaryResponse:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        request = Request(url, headers=dict(headers))
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS caller
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > max_bytes:
                raise ValueError("binary response exceeds the size limit")
            body = response.read(max_bytes + 1)
            content_type = response.headers.get("Content-Type", "").partition(";")[0].strip()
        if len(body) > max_bytes:
            raise ValueError("binary response exceeds the size limit")
        return BinaryResponse(
            body=body,
            content_type=content_type.casefold(),
            final_url=response.geturl(),
        )
