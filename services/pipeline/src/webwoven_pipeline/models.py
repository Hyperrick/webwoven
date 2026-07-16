from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Relation:
    key: str
    forward_label: str
    inverse_label: str | None
    category: str
    max_targets: int = 8
    playable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Entity:
    id: str
    label: str
    description: str
    entity_type: str
    category: str
    image_path: str | None = None
    image_attribution: dict[str, Any] | None = None
    wikipedia_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Edge:
    id: str
    source_id: str
    target_id: str
    relation_key: str
    statement_id: str
    explanation: str
    inverse: bool = False
    playable: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Round:
    id: str
    start_id: str
    target_id: str
    category: str
    difficulty: str
    optimal_distance: int
    time_window: int
    published: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MediaRecord:
    file_name: str
    original_url: str
    derivative_url: str
    source_url: str
    license_id: str
    creator: str
    license_url: str
    attribution_text: str
    restrictions: str = ""
    explicit_attribution: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return the public attribution fields embedded in graph entities."""
        return {
            "file_name": self.file_name,
            "original_url": self.original_url,
            "derivative_url": self.derivative_url,
            "source_url": self.source_url,
            "license_id": self.license_id,
            "creator": self.creator,
            "license_url": self.license_url,
            "attribution_text": self.attribution_text,
        }

    def policy_evidence(self) -> dict[str, str]:
        """Return source metadata needed to re-check an automatic license decision."""
        return {
            "restrictions": self.restrictions,
            "explicit_attribution": self.explicit_attribution,
        }


@dataclass(frozen=True, slots=True)
class Fact:
    id: str
    subject: str
    relation: str
    object: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ContentRequest:
    round_id: str
    start_label: str
    target_label: str
    target_aliases: tuple[str, ...]
    facts: tuple[Fact, ...]


@dataclass(frozen=True, slots=True)
class GeneratedContent:
    round_id: str
    hints: tuple[dict[str, Any], ...]
    explanations: tuple[dict[str, str], ...]
    recap: str
    provenance: dict[str, Any] = field(default_factory=dict[str, Any])

    def content_dict(self) -> dict[str, Any]:
        return {
            "hints": [dict(item) for item in self.hints],
            "explanations": [dict(item) for item in self.explanations],
            "recap": self.recap,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_id": self.round_id,
            **self.content_dict(),
            "provenance": self.provenance,
        }
