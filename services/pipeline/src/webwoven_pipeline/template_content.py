from __future__ import annotations

from typing import Any

from .content_contract import PROMPT_VERSION, fact_pack_sha256, output_sha256
from .content_validation import validate_content
from .models import ContentRequest, GeneratedContent


class DeterministicFallback:
    """Always-available copy derived only from the supplied verified facts."""

    def generate(self, request: ContentRequest) -> GeneratedContent:
        if not request.facts:
            raise ValueError("at least one verified fact is required")
        first = request.facts[0]
        middle = request.facts[len(request.facts) // 2]
        bridge = _safe_bridge(request)
        hints: list[dict[str, Any]] = [
            {
                "kind": "compass",
                "text": f"This route uses a {first.relation} connection.",
                "fact_ids": [first.id],
            },
            {
                "kind": "lens",
                "text": f"Look for an entity linked through {middle.relation}.",
                "fact_ids": [middle.id],
            },
            {
                "kind": "map_fragment",
                "text": f"A future bridge on the route is {bridge[0]}.",
                "fact_ids": [bridge[1]],
            },
        ]
        explanations: list[dict[str, str]] = [
            {
                "fact_id": fact.id,
                "text": f"{fact.subject} connects to {fact.object} through {fact.relation}.",
            }
            for fact in request.facts
        ]
        recap = (
            f"The route from {request.start_label} to {request.target_label} followed "
            f"{len(request.facts)} verified knowledge connections."
        )
        payload: dict[str, Any] = {
            "hints": hints,
            "explanations": explanations,
            "recap": recap,
        }
        validate_content(payload, request)
        return GeneratedContent(
            round_id=request.round_id,
            hints=tuple(hints),
            explanations=tuple(explanations),
            recap=recap,
            provenance={
                "generator": "deterministic_fallback",
                "prompt_version": PROMPT_VERSION,
                "fact_pack_sha256": fact_pack_sha256(request),
                "output_sha256": output_sha256(payload),
                "validation_results": [
                    "schema:passed",
                    "grounding:passed",
                    "answer_leak:passed",
                    "language:passed",
                ],
                "approval_status": "fallback",
            },
        )


def _safe_bridge(request: ContentRequest) -> tuple[str, str]:
    target_names = {
        request.target_label.casefold(),
        *(item.casefold() for item in request.target_aliases),
    }
    for fact in request.facts:
        if fact.object.casefold() not in target_names:
            return fact.object, fact.id
    for fact in request.facts:
        if fact.subject.casefold() not in target_names:
            return fact.subject, fact.id
    raise ValueError("fact pack does not contain a non-target bridge")
