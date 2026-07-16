from webwoven_pipeline.reviewed_media import (
    REVIEWED_MEDIA_CANDIDATES,
    REVIEWED_MEDIA_OVERRIDES,
)


def test_reviewed_tail_media_documents_its_entity_specific_match() -> None:
    candidate = REVIEWED_MEDIA_CANDIDATES["Q23017623"][0]

    assert candidate.file_name == "Cerous nitrate 6 water.png"
    assert candidate.provenance.startswith("reviewed_commons_work_by_subject:")


def test_reviewed_override_replaces_an_oversized_direct_animation_file() -> None:
    candidate = REVIEWED_MEDIA_OVERRIDES["Q11425"]

    assert candidate.file_name == "Phenakistiscope.jpg"
    assert candidate.provenance.startswith("reviewed_commons_documentary_subject:")
