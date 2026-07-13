from __future__ import annotations

import pytest
from webwoven_pipeline.relation_sentences import format_relation_sentence

RELATION_CASES = (
    ("P17", "Source is in Target.", "Target is in Source."),
    ("P19", "Source was born in Target.", "Target was born in Source."),
    ("P36", "Target is the capital of Source.", "Source is the capital of Target."),
    ("P50", "Source was written by Target.", "Target was written by Source."),
    ("P57", "Source was directed by Target.", "Target was directed by Source."),
    (
        "P61",
        "Source was discovered or invented by Target.",
        "Target was discovered or invented by Source.",
    ),
    ("P69", "Source studied at Target.", "Target studied at Source."),
    ("P108", "Source worked for Target.", "Target worked for Source."),
    ("P131", "Source is located in Target.", "Target is located in Source."),
    ("P138", "Source was named after Target.", "Target was named after Source."),
    (
        "P161",
        "Target appeared in the cast of Source.",
        "Source appeared in the cast of Target.",
    ),
    ("P166", "Source received Target.", "Target received Source."),
    ("P170", "Source was created by Target.", "Target was created by Source."),
    (
        "P171",
        "Source is classified directly under Target.",
        "Target is classified directly under Source.",
    ),
    ("P175", "Source was performed by Target.", "Target was performed by Source."),
    ("P276", "Source is located at Target.", "Target is located at Source."),
    ("P361", "Source is part of Target.", "Target is part of Source."),
    ("P463", "Source is a member of Target.", "Target is a member of Source."),
    ("P737", "Source was influenced by Target.", "Target was influenced by Source."),
    (
        "P800",
        "Target is a notable work by Source.",
        "Source is a notable work by Target.",
    ),
)


@pytest.mark.parametrize(("relation_key", "forward", "backward"), RELATION_CASES)
def test_relation_sentence_is_explicit_in_both_directions(
    relation_key: str,
    forward: str,
    backward: str,
) -> None:
    assert format_relation_sentence(relation_key, "Source", "Target", inverse=False) == forward
    assert format_relation_sentence(relation_key, "Source", "Target", inverse=True) == backward


def test_relation_sentences_cover_every_playable_registry_property(registry) -> None:
    assert {case[0] for case in RELATION_CASES} == registry.playable_keys


def test_unknown_relation_uses_truthful_generic_fallback() -> None:
    assert (
        format_relation_sentence("P999999", "Alpha", "Beta", inverse=False)
        == "Alpha has a documented connection to Beta."
    )


def test_ambiguous_relation_examples_read_as_complete_facts() -> None:
    assert (
        format_relation_sentence("P737", "Tobin Rill", "Orra Venn", inverse=False)
        == "Tobin Rill was influenced by Orra Venn."
    )
    assert (
        format_relation_sentence("P800", "Paper Moon Libretto", "Sera Loom", inverse=True)
        == "Paper Moon Libretto is a notable work by Sera Loom."
    )
