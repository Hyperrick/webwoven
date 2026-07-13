from __future__ import annotations

from collections.abc import Iterable

from .copy_vocabulary import SAFE_COPY_TOKENS
from .models import Fact
from .text_tokens import text_tokens


class FactGroundingError(ValueError):
    """Raised when copy contains claims outside its cited fact surfaces."""


def validate_fact_grounding(
    text: str,
    facts: Iterable[Fact],
    *,
    context_values: Iterable[str] = (),
    derived_tokens: Iterable[str] = (),
) -> None:
    """Allow only cited fact values, explicit context, and claim-neutral copy words."""

    fact_tokens = _fact_tokens(facts)
    context_tokens = {token for value in context_values for token in text_tokens(value)}
    allowed_derived = {token.casefold() for token in derived_tokens}
    allowed = fact_tokens | context_tokens | allowed_derived | SAFE_COPY_TOKENS
    actual = set(text_tokens(text))
    unsupported = sorted(actual - allowed)
    if unsupported:
        preview = ", ".join(unsupported[:5])
        raise FactGroundingError(f"copy contains unsupported fact tokens: {preview}")

    evidence = fact_tokens - SAFE_COPY_TOKENS
    if not actual.intersection(evidence):
        raise FactGroundingError("copy does not include a value from its cited facts")


def _fact_tokens(facts: Iterable[Fact]) -> set[str]:
    return {
        token
        for fact in facts
        for value in (fact.subject, fact.relation, fact.object)
        for token in text_tokens(value)
    }
