from __future__ import annotations

import re

TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", re.UNICODE)


def text_tokens(text: str) -> tuple[str, ...]:
    """Return stable, case-folded word and number tokens for validation."""

    normalized: list[str] = []
    for match in TOKEN_PATTERN.findall(text.casefold()):
        token = match.replace("’", "'")
        if token.endswith("'s") and len(token) > 2:
            token = token[:-2]
        normalized.append(token)
    return tuple(normalized)
