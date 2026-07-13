from __future__ import annotations

import json
from collections.abc import Mapping
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
