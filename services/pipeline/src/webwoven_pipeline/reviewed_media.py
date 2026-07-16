from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReviewedMediaCandidate:
    file_name: str
    provenance: str


# Human-reviewed tail candidates must show a documented, entity-specific link.
REVIEWED_MEDIA_CANDIDATES = {
    "Q23017623": (
        ReviewedMediaCandidate(
            "Cerous nitrate 6 water.png",
            "reviewed_commons_work_by_subject:Ludwig Camillo Haitinger:1907",
        ),
    ),
}
