from __future__ import annotations

import pytest
from webwoven_pipeline.relation_semantics import (
    RelationEntityProfile,
    is_language,
    is_organization,
    is_place,
)
from webwoven_pipeline.relation_sentences import format_relation_sentence

RELATION_CASES = (
    ("P17", "Source is associated with Target.", "Target is associated with Source."),
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
    (
        "P166",
        "Source has a recorded recognition connection to the Target.",
        "Target has a recorded recognition connection to the Source.",
    ),
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


def test_ranked_selection_beats_award_classification_and_preserves_ordinal() -> None:
    work = RelationEntityProfile("Animal Farm", "1945 novella by George Orwell")
    selection = RelationEntityProfile(
        "NPR Top 100 Science Fiction and Fantasy Books",
        "literature award in 2011 based on public votes",
        classification_ids=frozenset({"Q378427", "Q49958"}),
    )
    expected = "Animal Farm ranked #13 on the NPR Top 100 Science Fiction and Fantasy Books."

    assert (
        format_relation_sentence(
            "P166",
            work,
            selection,
            inverse=False,
            series_ordinal="13",
        )
        == expected
    )
    assert (
        format_relation_sentence(
            "P166",
            selection,
            work,
            inverse=True,
            series_ordinal="13",
        )
        == expected
    )


def test_ranked_selection_without_ordinal_uses_inclusion_wording() -> None:
    selection = RelationEntityProfile(
        "Readers' 50 Favourite Novels",
        classification_ids=frozenset({"Q49958"}),
    )

    assert (
        format_relation_sentence("P166", "Novel", selection, inverse=False)
        == "Novel was included in Readers' 50 Favourite Novels."
    )


@pytest.mark.parametrize(
    ("selection", "display_label"),
    [
        (
            RelationEntityProfile(
                "Le Monde's 100 Books of the Century",
                "Wikimedia list article",
            ),
            "Le Monde's 100 Books of the Century",
        ),
        (
            RelationEntityProfile(
                "National Board of Review: Top Ten Films",
                "film award",
            ),
            "the National Board of Review: Top Ten Films",
        ),
        (
            RelationEntityProfile(
                "Time 100",
                "Time Magazine's annual listing of 100 influential people",
            ),
            "the Time 100",
        ),
    ],
)
def test_other_ranked_selection_shapes_use_inclusion_wording(
    selection: RelationEntityProfile,
    display_label: str,
) -> None:
    assert (
        format_relation_sentence("P166", "Example", selection, inverse=False)
        == f"Example was included in {display_label}."
    )


def test_actual_award_keeps_award_wording() -> None:
    award = RelationEntityProfile(
        "Nebula Award for Best Novel",
        classification_ids=frozenset({"Q378427"}),
    )

    assert (
        format_relation_sentence("P166", "The Left Hand of Darkness", award, inverse=False)
        == "The Left Hand of Darkness received the Nebula Award for Best Novel."
    )


def test_award_description_mentioning_winner_list_remains_an_award() -> None:
    award = RelationEntityProfile(
        "Annie Award for Best Animated Feature",
        "list of award winners",
    )
    assert (
        format_relation_sentence("P166", "Spirited Away", award, inverse=False)
        == "Spirited Away received the Annie Award for Best Animated Feature."
    )


@pytest.mark.parametrize(
    "description",
    [
        "language regulator of Italian",
        "family of markup languages for displaying content in a web browser",
        "English-language public research university",
        "literary prize for English language literature",
        "association for scholars of language and literature",
        "prize honoring contributions to the Dutch language",
    ],
)
def test_language_semantics_require_structured_positive_evidence(description: str) -> None:
    assert not is_language(RelationEntityProfile("Subject", description))


def test_language_semantics_accept_class_or_explicit_source_tag() -> None:
    assert is_language(RelationEntityProfile("English", classification_ids=frozenset({"Q33742"})))
    assert is_language(
        RelationEntityProfile("Provider language", semantic_tags=frozenset({"language"}))
    )


def test_place_and_organization_semantics_require_structured_positive_evidence() -> None:
    assert not is_place(
        RelationEntityProfile("Bombe", "codebreaking device created at Bletchley Park")
    )
    assert not is_organization(
        RelationEntityProfile(
            "Bauhaus and its Sites in Weimar, Dessau and Bernau",
            "World Heritage Site associated with the Bauhaus art school",
        )
    )


@pytest.mark.parametrize(
    ("country", "expected"),
    [
        ("People's Republic of China", "the People's Republic of China"),
        ("Russian Empire", "the Russian Empire"),
        ("European Union", "the European Union"),
        ("Kingdom of Denmark", "the Kingdom of Denmark"),
        ("Japan", "Japan"),
    ],
)
def test_country_relationship_applies_deterministic_articles(
    country: str,
    expected: str,
) -> None:
    subject = RelationEntityProfile("Example", semantic_tags=frozenset({"organization"}))

    assert (
        format_relation_sentence("P17", subject, country, inverse=False)
        == f"Example is based in {expected}."
    )


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("ORCID, Inc.", "Source worked for ORCID, Inc."),
        ("Help!", "Source worked for Help!"),
    ],
)
def test_sentence_finalizer_does_not_duplicate_label_punctuation(
    target: str,
    expected: str,
) -> None:
    assert format_relation_sentence("P108", "Source", target, inverse=False) == expected


@pytest.mark.parametrize(
    ("subject", "expected"),
    [
        (
            RelationEntityProfile("English", classification_ids=frozenset({"Q33742"})),
            "English is used in the United States.",
        ),
        (
            RelationEntityProfile(
                "Nebula Award for Best Novel",
                classification_ids=frozenset({"Q378427"}),
            ),
            "Nebula Award for Best Novel is associated with the United States.",
        ),
        (
            RelationEntityProfile("Chicago", classification_ids=frozenset({"Q515"})),
            "Chicago is in the United States.",
        ),
        (
            RelationEntityProfile(
                "Example Academy",
                "national academy of sciences",
                semantic_tags=frozenset({"organization"}),
            ),
            "Example Academy is based in the United States.",
        ),
        (
            RelationEntityProfile(
                "Bavarian Order of Merit",
                "state decoration of Bavaria",
                semantic_tags=frozenset({"recognition"}),
            ),
            "Bavarian Order of Merit is associated with the United States.",
        ),
        (
            RelationEntityProfile("Bombe", "codebreaking device created at Bletchley Park"),
            "Bombe is associated with the United States.",
        ),
        (
            RelationEntityProfile(
                "Bauhaus and its Sites in Weimar, Dessau and Bernau",
                "World Heritage Site associated with the Bauhaus art school",
            ),
            (
                "Bauhaus and its Sites in Weimar, Dessau and Bernau is associated with "
                "the United States."
            ),
        ),
    ],
)
def test_country_relationship_uses_subject_semantics(
    subject: RelationEntityProfile,
    expected: str,
) -> None:
    country = RelationEntityProfile("United States", classification_ids=frozenset({"Q6256"}))

    assert format_relation_sentence("P17", subject, country, inverse=False) == expected
    assert format_relation_sentence("P17", country, subject, inverse=True) == expected
