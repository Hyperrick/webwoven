from __future__ import annotations

import hashlib
import json

from .models import ContentRequest

PROMPT_VERSION = "webwoven-content-v1"


def fact_pack_sha256(request: ContentRequest) -> str:
    return _hash([fact.to_dict() for fact in request.facts])


def output_sha256(payload: object) -> str:
    return _hash(payload)


def prompt_sha256(prompt_text: str) -> str:
    return hashlib.sha256(prompt_text.encode()).hexdigest()


def _hash(value: object) -> str:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()
