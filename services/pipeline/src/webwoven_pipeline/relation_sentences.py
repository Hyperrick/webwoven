from __future__ import annotations

from typing import Final

# Templates receive labels in navigation order: source is the current entity and
# target is the reachable entity. Inverse templates restore the underlying fact's
# natural subject/object order instead of exposing database relation vocabulary.
_RELATION_SENTENCES: Final[dict[str, tuple[str, str]]] = {
    "P17": (
        "{source} is in {target}.",
        "{target} is in {source}.",
    ),
    "P19": (
        "{source} was born in {target}.",
        "{target} was born in {source}.",
    ),
    "P36": (
        "{target} is the capital of {source}.",
        "{source} is the capital of {target}.",
    ),
    "P50": (
        "{source} was written by {target}.",
        "{target} was written by {source}.",
    ),
    "P57": (
        "{source} was directed by {target}.",
        "{target} was directed by {source}.",
    ),
    "P61": (
        "{source} was discovered or invented by {target}.",
        "{target} was discovered or invented by {source}.",
    ),
    "P69": (
        "{source} studied at {target}.",
        "{target} studied at {source}.",
    ),
    "P108": (
        "{source} worked for {target}.",
        "{target} worked for {source}.",
    ),
    "P131": (
        "{source} is located in {target}.",
        "{target} is located in {source}.",
    ),
    "P138": (
        "{source} was named after {target}.",
        "{target} was named after {source}.",
    ),
    "P161": (
        "{target} appeared in the cast of {source}.",
        "{source} appeared in the cast of {target}.",
    ),
    "P166": (
        "{source} received {target}.",
        "{target} received {source}.",
    ),
    "P170": (
        "{source} was created by {target}.",
        "{target} was created by {source}.",
    ),
    "P171": (
        "{source} is classified directly under {target}.",
        "{target} is classified directly under {source}.",
    ),
    "P175": (
        "{source} was performed by {target}.",
        "{target} was performed by {source}.",
    ),
    "P276": (
        "{source} is located at {target}.",
        "{target} is located at {source}.",
    ),
    "P361": (
        "{source} is part of {target}.",
        "{target} is part of {source}.",
    ),
    "P463": (
        "{source} is a member of {target}.",
        "{target} is a member of {source}.",
    ),
    "P737": (
        "{source} was influenced by {target}.",
        "{target} was influenced by {source}.",
    ),
    "P800": (
        "{target} is a notable work by {source}.",
        "{source} is a notable work by {target}.",
    ),
}


def format_relation_sentence(
    relation_key: str,
    source_label: str,
    target_label: str,
    *,
    inverse: bool,
) -> str:
    """Describe one navigable edge as a complete fact-grounded English sentence."""
    templates = _RELATION_SENTENCES.get(relation_key)
    if templates is None:
        return f"{source_label} has a documented connection to {target_label}."
    template = templates[1 if inverse else 0]
    return template.format(source=source_label, target=target_label)
