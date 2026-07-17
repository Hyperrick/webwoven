from dataclasses import replace
from pathlib import Path

import pytest
from webwoven_pipeline.compiler import GraphCompileError, compile_graph
from webwoven_pipeline.fixture import build_smoke_graph
from webwoven_pipeline.models import Edge, Entity


@pytest.mark.parametrize(
    "explanation",
    [
        "Animal Farm received NPR Top 100 Science Fiction and Fantasy Books.",
        "Animal Farm won NPR Top 100 Science Fiction and Fantasy Books.",
        "Animal Farm was awarded NPR Top 100 Science Fiction and Fantasy Books.",
        "Animal Farm was granted NPR Top 100 Science Fiction and Fantasy Books.",
        "Animal Farm was honored with NPR Top 100 Science Fiction and Fantasy Books.",
    ],
)
@pytest.mark.parametrize("inverse", [False, True])
def test_compiler_rejects_award_wording_for_a_ranked_selection(
    tmp_path: Path,
    registry,
    explanation: str,
    inverse: bool,
) -> None:
    work = _entity("Q1", "Animal Farm", "1945 novella by George Orwell")
    selection = _entity(
        "Q2",
        "NPR Top 100 Science Fiction and Fantasy Books",
        "literature selection in 2011 based on public votes",
    )
    edge = _edge(
        work,
        selection,
        relation_key="P166",
        explanation=explanation,
        inverse=inverse,
    )

    with pytest.raises(GraphCompileError, match="award wording for ranked selection"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (work, selection), (edge,), ())


def test_compiler_accepts_ranking_wording_for_a_ranked_selection(
    tmp_path: Path,
    registry,
) -> None:
    work = _entity("Q1", "Animal Farm", "1945 novella by George Orwell")
    selection = _entity(
        "Q2",
        "NPR Top 100 Science Fiction and Fantasy Books",
        "literature selection in 2011 based on public votes",
    )
    edge = replace(
        _edge(
            work,
            selection,
            relation_key="P166",
            explanation=(
                "Animal Farm ranked #13 on the NPR Top 100 Science Fiction and Fantasy Books."
            ),
        ),
        series_ordinal="13",
    )

    compile_graph(tmp_path / "graph.sqlite3", registry, (work, selection), (edge,), ())


def test_compiler_does_not_treat_award_in_an_entity_label_as_award_wording(
    tmp_path: Path,
    registry,
) -> None:
    selection = _entity(
        "Q1",
        "National Board of Review: Top Ten Films",
        "annual film selection",
        semantic_tags=("ranked_selection",),
    )
    award = _entity(
        "Q2",
        "National Board of Review Award for Best Actress",
        "film award",
        semantic_tags=("award",),
    )
    edge = _edge(
        award,
        selection,
        relation_key="P166",
        explanation=(
            "National Board of Review Award for Best Actress was included in the "
            "National Board of Review: Top Ten Films."
        ),
    )

    compile_graph(tmp_path / "graph.sqlite3", registry, (selection, award), (edge,), ())


def test_compiler_accepts_award_wording_when_description_mentions_winner_list(
    tmp_path: Path,
    registry,
) -> None:
    work = _entity("Q1", "Spirited Away", "2001 animated film")
    award = _entity(
        "Q2",
        "Annie Award for Best Animated Feature",
        "list of award winners",
    )
    edge = _edge(
        work,
        award,
        relation_key="P166",
        explanation="Spirited Away received the Annie Award for Best Animated Feature.",
    )

    compile_graph(tmp_path / "graph.sqlite3", registry, (work, award), (edge,), ())


def test_compiler_requires_semantic_evidence_for_generic_recognition(
    tmp_path: Path,
    registry,
) -> None:
    work = _entity("Q1", "Example", "provider work")
    ambiguous = _entity("Q2", "Readers Choice", "provider-authored collection")
    edge = _edge(
        work,
        ambiguous,
        relation_key="P166",
        explanation="Example has a recorded recognition connection to the Readers Choice.",
    )

    with pytest.raises(GraphCompileError, match="lacks semantic recognition evidence"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (work, ambiguous), (edge,), ())


def test_compiler_accepts_explicit_neutral_recognition_evidence(
    tmp_path: Path,
    registry,
) -> None:
    work = _entity("Q1", "Example", "provider work")
    recognition = _entity(
        "Q2",
        "Readers Choice",
        "provider-authored collection",
        semantic_tags=("recognition",),
    )
    edge = _edge(
        work,
        recognition,
        relation_key="P166",
        explanation="Example has a recorded recognition connection to the Readers Choice.",
    )

    compile_graph(tmp_path / "graph.sqlite3", registry, (work, recognition), (edge,), ())


def test_compiler_rejects_award_wording_for_neutral_recognition(
    tmp_path: Path,
    registry,
) -> None:
    work = _entity("Q1", "Example", "provider work")
    recognition = _entity(
        "Q2",
        "Readers Choice",
        "provider-authored collection",
        semantic_tags=("recognition",),
    )
    edge = _edge(
        work,
        recognition,
        relation_key="P166",
        explanation="Example received the Readers Choice.",
    )

    with pytest.raises(GraphCompileError, match="award wording without award evidence"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (work, recognition), (edge,), ())


@pytest.mark.parametrize(
    ("label", "description", "semantic_tags"),
    [
        ("English", "West Germanic language", ()),
        ("Nebula Award for Best Novel", "science fiction and fantasy literary award", ()),
        ("Royal Society", "national academy of sciences and learned society", ()),
        ("Century Reading List", "curated collection", ("ranked_selection",)),
        ("Bombe", "codebreaking device created at Bletchley Park", ()),
        ("Bavarian Order of Merit", "state decoration of Bavaria", ("recognition",)),
        (
            "Bauhaus and its Sites in Weimar, Dessau and Bernau",
            "World Heritage Site associated with the Bauhaus art school",
            (),
        ),
    ],
)
@pytest.mark.parametrize(
    "wording",
    ["is in", "was located in", "is situated within", "lies in"],
)
@pytest.mark.parametrize("inverse", [False, True])
def test_compiler_rejects_physical_wording_for_non_place_country_subjects(
    tmp_path: Path,
    registry,
    label: str,
    description: str,
    semantic_tags: tuple[str, ...],
    wording: str,
    inverse: bool,
) -> None:
    subject = _entity("Q1", label, description, semantic_tags=semantic_tags)
    country = _entity("Q2", "United States", "country in North America")
    edge = _edge(
        subject,
        country,
        relation_key="P17",
        explanation=f"{label} {wording} United States.",
        inverse=inverse,
    )

    with pytest.raises(GraphCompileError, match="place wording for non-place subject"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (subject, country), (edge,), ())


@pytest.mark.parametrize(
    ("label", "description", "semantic_tags", "country_label", "explanation"),
    [
        (
            "English",
            "West Germanic language",
            ("language",),
            "United States",
            "English is used in the United States.",
        ),
        (
            "Nebula Award for Best Novel",
            "science fiction literary award",
            ("award",),
            "United States",
            "Nebula Award for Best Novel is associated with the United States.",
        ),
        (
            "Royal Society",
            "learned society",
            ("organization",),
            "United Kingdom",
            "Royal Society is based in the United Kingdom.",
        ),
    ],
)
def test_compiler_accepts_precise_country_wording_for_non_place_subjects(
    tmp_path: Path,
    registry,
    label: str,
    description: str,
    semantic_tags: tuple[str, ...],
    country_label: str,
    explanation: str,
) -> None:
    subject = _entity("Q1", label, description, semantic_tags=semantic_tags)
    country = _entity("Q2", country_label, "sovereign state")
    edge = _edge(
        subject,
        country,
        relation_key="P17",
        explanation=explanation,
    )

    compile_graph(tmp_path / "graph.sqlite3", registry, (subject, country), (edge,), ())


def test_compiler_rejects_explanation_about_different_entities(tmp_path: Path, registry) -> None:
    subject = _entity("Q1", "Subject", "provider subject")
    object_value = _entity("Q2", "Object", "provider object")
    edge = _edge(
        subject,
        object_value,
        relation_key="P361",
        explanation="English is used in the United States.",
    )

    with pytest.raises(GraphCompileError, match="does not mention statement subject 'Subject'"):
        compile_graph(
            tmp_path / "graph.sqlite3",
            registry,
            (subject, object_value),
            (edge,),
            (),
        )


@pytest.mark.parametrize(
    ("semantic_tags", "explanation", "error"),
    [
        ((), "Example is used in the United States.", "language wording for non-language"),
        ((), "Example is based in the United States.", "organization wording for non-organization"),
    ],
)
def test_compiler_rejects_unsubstantiated_country_verbs(
    tmp_path: Path,
    registry,
    semantic_tags: tuple[str, ...],
    explanation: str,
    error: str,
) -> None:
    subject = _entity("Q1", "Example", "provider subject", semantic_tags=semantic_tags)
    country = _entity("Q2", "United States", "sovereign state")
    edge = _edge(subject, country, relation_key="P17", explanation=explanation)

    with pytest.raises(GraphCompileError, match=error):
        compile_graph(tmp_path / "graph.sqlite3", registry, (subject, country), (edge,), ())


def test_compiler_rejects_noncanonical_country_claim(tmp_path: Path, registry) -> None:
    subject = _entity("Q1", "HTML", "markup language")
    country = _entity("Q2", "United Kingdom", "sovereign state")
    edge = _edge(
        subject,
        country,
        relation_key="P17",
        explanation="HTML is the official language of the United Kingdom.",
    )

    with pytest.raises(GraphCompileError, match="does not use canonical P17 wording"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (subject, country), (edge,), ())


def test_compiler_rejects_noncanonical_neutral_recognition_claim(
    tmp_path: Path,
    registry,
) -> None:
    work = _entity("Q1", "Example", "provider work")
    recognition = _entity(
        "Q2",
        "Readers Choice",
        "provider-authored collection",
        semantic_tags=("recognition",),
    )
    edge = _edge(
        work,
        recognition,
        relation_key="P166",
        explanation="Example earned the Readers Choice.",
    )

    with pytest.raises(GraphCompileError, match="does not use canonical P166 wording"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (work, recognition), (edge,), ())


def test_compiler_matches_overlapping_endpoint_labels(tmp_path: Path, registry) -> None:
    city = _entity("Q1", "New York City", "city")
    state = _entity("Q2", "New York", "state")
    edge = _edge(
        city,
        state,
        relation_key="P131",
        explanation="New York City is located in New York.",
    )

    compile_graph(tmp_path / "graph.sqlite3", registry, (city, state), (edge,), ())


def test_compiler_requires_two_mentions_for_same_label_endpoints(
    tmp_path: Path,
    registry,
) -> None:
    planet = _entity("Q1", "Mars", "planet")
    deity = _entity("Q2", "Mars", "Roman deity")
    edge = _edge(
        planet,
        deity,
        relation_key="P138",
        explanation="Mars is a planet.",
    )

    with pytest.raises(GraphCompileError, match="does not mention statement object 'Mars'"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (planet, deity), (edge,), ())

    complete_edge = replace(edge, explanation="Mars was named after Mars.")
    compile_graph(
        tmp_path / "complete.sqlite3",
        registry,
        (planet, deity),
        (complete_edge,),
        (),
    )


def test_compiler_accepts_is_in_for_a_place(tmp_path: Path, registry) -> None:
    place = _entity(
        "Q1",
        "South Kestrel District",
        "fictional coastal district",
        semantic_tags=("place",),
    )
    country = _entity("Q2", "Republic of Avenmark", "fictional country")
    edge = _edge(
        place,
        country,
        relation_key="P17",
        explanation="South Kestrel District is in the Republic of Avenmark.",
    )

    compile_graph(tmp_path / "graph.sqlite3", registry, (place, country), (edge,), ())


def test_compiler_accepts_the_existing_smoke_fixture(tmp_path: Path, registry) -> None:
    entities, edges = build_smoke_graph()

    compile_graph(tmp_path / "graph.sqlite3", registry, entities, edges, ())


@pytest.mark.parametrize(
    "explanation",
    [
        " Leading whitespace.",
        "Trailing whitespace. ",
        "Two lines.\nSecond line.",
        "No terminal punctuation",
        "Source is \u00adpart of Target.",
    ],
)
def test_compiler_rejects_malformed_explanations(
    tmp_path: Path,
    registry,
    explanation: str,
) -> None:
    source = _entity("Q1", "Source", "example subject")
    target = _entity("Q2", "Target", "example object")

    with pytest.raises(GraphCompileError, match="explanation"):
        compile_graph(
            tmp_path / "graph.sqlite3",
            registry,
            (source, target),
            (_edge(source, target, relation_key="P361", explanation=explanation),),
            (),
        )


def test_compiler_rejects_duplicate_terminal_punctuation(tmp_path: Path, registry) -> None:
    source = _entity("Q1", "Source", "example subject")
    target = _entity("Q2", "ORCID, Inc.", "example organization")
    edge = _edge(
        source,
        target,
        relation_key="P108",
        explanation="Source worked for ORCID, Inc..",
    )

    with pytest.raises(GraphCompileError, match="duplicated terminal punctuation"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (source, target), (edge,), ())


def test_entity_label_named_won_cannot_hide_award_wording(tmp_path: Path, registry) -> None:
    work = _entity("Q1", "Won", "fictional work")
    selection = _entity(
        "Q2",
        "Top 100 Films",
        "ranked film selection",
        semantic_tags=("ranked_selection",),
    )
    edge = _edge(
        work,
        selection,
        relation_key="P166",
        explanation="Won won the Top 100 Films.",
    )

    with pytest.raises(GraphCompileError, match="award wording for ranked selection"):
        compile_graph(tmp_path / "graph.sqlite3", registry, (work, selection), (edge,), ())


def test_compiler_rejects_direction_dependent_copy(tmp_path: Path, registry) -> None:
    work = _entity("Q1", "Example Book", "fictional book")
    author = _entity("Q2", "Example Author", "fictional writer")
    forward = _edge(
        work,
        author,
        relation_key="P50",
        explanation="Example Book was written by Example Author.",
    )
    inverse = replace(
        _edge(
            work,
            author,
            relation_key="P50",
            explanation="Example Book was written by Example Author.",
            inverse=True,
        ),
        explanation="Example Author wrote Example Book.",
    )

    with pytest.raises(GraphCompileError, match="changes explanation by direction"):
        compile_graph(
            tmp_path / "graph.sqlite3",
            registry,
            (work, author),
            (forward, inverse),
            (),
        )


def test_compiler_rejects_direction_dependent_playability(tmp_path: Path, registry) -> None:
    work = _entity("Q1", "Example Book", "fictional book")
    author = _entity("Q2", "Example Author", "fictional writer")
    forward = _edge(
        work,
        author,
        relation_key="P50",
        explanation="Example Book was written by Example Author.",
    )
    inverse = replace(
        _edge(
            work,
            author,
            relation_key="P50",
            explanation="Example Book was written by Example Author.",
            inverse=True,
        ),
        playable=False,
    )

    with pytest.raises(GraphCompileError, match="changes playability by direction"):
        compile_graph(
            tmp_path / "graph.sqlite3",
            registry,
            (work, author),
            (forward, inverse),
            (),
        )


def _entity(
    entity_id: str,
    label: str,
    description: str,
    *,
    semantic_tags: tuple[str, ...] = (),
) -> Entity:
    return Entity(
        entity_id,
        label,
        description,
        "imported_item",
        "test",
        semantic_tags=semantic_tags,
    )


def _edge(
    subject: Entity,
    object_value: Entity,
    *,
    relation_key: str,
    explanation: str,
    inverse: bool = False,
) -> Edge:
    source, target = (object_value, subject) if inverse else (subject, object_value)
    return Edge(
        id=f"edge:{relation_key}:{'inverse' if inverse else 'forward'}",
        source_id=source.id,
        target_id=target.id,
        relation_key=relation_key,
        statement_id="statement:1",
        explanation=explanation,
        inverse=inverse,
    )
