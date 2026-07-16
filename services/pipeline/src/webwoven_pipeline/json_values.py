from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast


def json_object(value: object) -> Mapping[str, Any]:
    """Narrow an untrusted JSON value to a string-keyed object."""
    if not isinstance(value, Mapping):
        return {}
    return cast(Mapping[str, Any], value)
