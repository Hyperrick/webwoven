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


# Direct Wikidata media can still fail the bounded raster download policy. These
# entity-specific replacements are documentary Commons files reviewed for that
# exact subject and still pass the normal license validator before publication.
REVIEWED_MEDIA_OVERRIDES = {
    "Q11425": ReviewedMediaCandidate(
        "Phenakistiscope.jpg",
        "reviewed_commons_documentary_subject:early_animation_device:1832",
    ),
}
