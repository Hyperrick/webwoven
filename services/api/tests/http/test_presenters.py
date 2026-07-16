"""Focused session-presentation tests for relation group identity."""

import json
from datetime import UTC, datetime
from unittest.mock import create_autospec

from webwoven_api.domain.navigation import follow_edge, start_navigation
from webwoven_api.domain.scoring import Difficulty
from webwoven_api.graph.contracts import Entity, GraphEdge, Round
from webwoven_api.graph.memory_reader import MemoryGraphReader
from webwoven_api.http.presentation.entities import entity_response
from webwoven_api.http.presentation.sessions import SessionPresenter
from webwoven_api.sessions.exploration import backed_frame, followed_frame
from webwoven_api.sessions.models import GameSession, SessionMode, SessionStatus
from webwoven_api.sessions.service import SessionService


def test_entity_response_exposes_only_complete_commons_attribution() -> None:
    attribution = {
        "file_name": "The Great Wave off Kanagawa.jpg",
        "original_url": "https://upload.wikimedia.org/original.jpg",
        "derivative_url": "https://upload.wikimedia.org/thumbnail.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:The_Great_Wave.jpg",
        "license_id": "PUBLIC_DOMAIN",
        "creator": "Katsushika Hokusai",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "attribution_text": ("Katsushika Hokusai — Public Domain — Wikimedia Commons"),
    }
    response = entity_response(
        Entity(
            "Q1",
            "The Great Wave",
            None,
            "work",
            "arts_culture",
            "/media/great-wave.jpg",
            json.dumps(attribution),
        )
    )

    assert response.image_attribution is not None
    assert response.image_attribution.creator == "Katsushika Hokusai"
    assert response.image_attribution.license_id == "PUBLIC_DOMAIN"
    assert str(response.image_attribution.source_url).startswith("https://commons.wikimedia.org/")


def test_entity_response_accepts_complete_share_alike_attribution() -> None:
    attribution = {
        "file_name": "Portrait.jpg",
        "original_url": "https://upload.wikimedia.org/original.jpg",
        "derivative_url": "https://upload.wikimedia.org/thumbnail.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Portrait.jpg",
        "license_id": "CC_BY_SA_4_0",
        "creator": "Example photographer",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "attribution_text": ("Example photographer — CC BY-SA 4.0 — Wikimedia Commons"),
        "context_label": "Related award recipient",
    }

    response = entity_response(
        Entity(
            "Q2",
            "Portrait",
            None,
            "work",
            "arts_culture",
            "/media/portrait.jpg",
            json.dumps(attribution),
        )
    )

    assert response.image_attribution is not None
    assert response.image_attribution.license_id == "CC_BY_SA_4_0"
    assert response.image_attribution.context_label == "Related award recipient"


def test_entity_response_accepts_official_commons_thumbnail_endpoint() -> None:
    attribution = {
        "file_name": "Small portrait.jpg",
        "original_url": "https://upload.wikimedia.org/small-portrait.jpg",
        "derivative_url": ("https://commons.wikimedia.org/w/thumb.php?f=Small+portrait.jpg&w=480"),
        "source_url": "https://commons.wikimedia.org/wiki/File:Small_portrait.jpg",
        "license_id": "CC0_1_0",
        "creator": "Example photographer",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "attribution_text": "Example photographer — CC0 1.0 — Wikimedia Commons",
    }

    response = entity_response(
        Entity(
            "Q3",
            "Small portrait",
            None,
            "work",
            "arts_culture",
            "/media/small-portrait.jpg",
            json.dumps(attribution),
        )
    )

    assert response.image_attribution is not None
    assert str(response.image_attribution.derivative_url).startswith(
        "https://commons.wikimedia.org/w/thumb.php?"
    )


def test_entity_response_accepts_a_ported_share_alike_license_url() -> None:
    attribution = {
        "file_name": "Portrait.jpg",
        "original_url": "https://upload.wikimedia.org/original.jpg",
        "derivative_url": "https://upload.wikimedia.org/thumbnail.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Portrait.jpg",
        "license_id": "CC_BY_SA_3_0",
        "creator": "Example photographer",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0/de/",
        "attribution_text": ("Example photographer — CC BY-SA 3.0 — Wikimedia Commons"),
    }

    response = entity_response(
        Entity(
            "Q3",
            "Portrait",
            None,
            "work",
            "arts_culture",
            "/media/portrait.jpg",
            json.dumps(attribution),
        )
    )

    assert response.image_attribution is not None
    assert str(response.image_attribution.license_url).endswith("/3.0/de/")


def test_entity_response_hides_malformed_or_incomplete_attribution() -> None:
    malformed = entity_response(
        Entity(
            "Q1",
            "The Great Wave",
            None,
            "work",
            "arts_culture",
            "/media/great-wave.jpg",
            '{"creator":"Katsushika Hokusai"}',
        )
    )
    unsupported_license = entity_response(
        Entity(
            "Q2",
            "Another image",
            None,
            "work",
            "arts_culture",
            "/media/other.jpg",
            json.dumps(
                {
                    "file_name": "Other.jpg",
                    "original_url": "https://upload.wikimedia.org/original.jpg",
                    "derivative_url": "https://upload.wikimedia.org/thumbnail.jpg",
                    "source_url": "https://commons.wikimedia.org/wiki/File:Other.jpg",
                    "license_id": "FAL_1_3",
                    "creator": "Creator",
                    "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                    "attribution_text": "Creator — CC BY-SA 4.0 — Wikimedia Commons",
                }
            ),
        )
    )
    mismatched_license_url = entity_response(
        Entity(
            "Q3",
            "Mismatched license",
            None,
            "work",
            "arts_culture",
            "/api/v1/media/mismatch.jpg",
            json.dumps(
                {
                    "file_name": "Mismatch.jpg",
                    "original_url": "https://upload.wikimedia.org/original.jpg",
                    "derivative_url": "https://upload.wikimedia.org/thumbnail.jpg",
                    "source_url": "https://commons.wikimedia.org/wiki/File:Mismatch.jpg",
                    "license_id": "CC_BY_4_0",
                    "creator": "Creator",
                    "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                    "attribution_text": "Creator — CC BY 4.0 — Wikimedia Commons",
                }
            ),
        )
    )
    missing_creator_credit = entity_response(
        Entity(
            "Q4",
            "Missing creator credit",
            None,
            "work",
            "arts_culture",
            "/api/v1/media/missing-credit.jpg",
            json.dumps(
                {
                    "file_name": "Missing credit.jpg",
                    "original_url": "https://upload.wikimedia.org/original.jpg",
                    "derivative_url": "https://upload.wikimedia.org/thumbnail.jpg",
                    "source_url": "https://commons.wikimedia.org/wiki/File:Missing_credit.jpg",
                    "license_id": "CC_BY_4_0",
                    "creator": "Named creator",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "attribution_text": "Some credit — CC BY 4.0 — Wikimedia Commons",
                }
            ),
        )
    )

    assert malformed.image_attribution is None
    assert malformed.image_path is None
    assert unsupported_license.image_attribution is None
    assert unsupported_license.image_path is None
    assert mismatched_license_url.image_attribution is None
    assert mismatched_license_url.image_path is None
    assert missing_creator_credit.image_attribution is None
    assert missing_creator_credit.image_path is None


def test_relation_groups_distinguish_forward_and_inverse_uses_of_one_property() -> None:
    entities = {
        "Q1": Entity("Q1", "Crossroads", None, "place", "places"),
        "Q2": Entity("Q2", "Forward target", None, "place", "places"),
        "Q3": Entity("Q3", "Inverse target", None, "place", "places"),
    }
    edges = (
        GraphEdge(
            id="edge-forward",
            source_id="Q1",
            target_id="Q2",
            relation_key="P36",
            relation_label="capital",
            statement_id="statement-forward",
            explanation="Forward target is the capital of Crossroads.",
            target=entities["Q2"],
            direction="outgoing",
        ),
        GraphEdge(
            id="edge-inverse",
            source_id="Q1",
            target_id="Q3",
            relation_key="P36",
            relation_label="capital of",
            statement_id="statement-inverse",
            explanation="Crossroads is the capital of Inverse target.",
            target=entities["Q3"],
            direction="incoming",
        ),
    )
    round_ = Round(
        id="round",
        start_id="Q1",
        target_id="Q2",
        category="places",
        difficulty=Difficulty.EASY,
        optimal_distance=1,
        time_window=120,
        published=True,
    )
    graph = MemoryGraphReader(
        entities=entities,
        edges=edges,
        rounds=(round_,),
        distances={("round", "Q1"): 1, ("round", "Q2"): 0},
    )
    session = GameSession(
        id="session",
        guest_id="guest",
        mode=SessionMode.SOLO,
        graph_version=graph.graph_version,
        round=round_,
        navigation=start_navigation("Q1"),
        status=SessionStatus.ACTIVE,
        state_version=0,
        started_at=datetime(2026, 7, 13, tzinfo=UTC),
    )
    sessions = create_autospec(SessionService, instance=True)
    sessions.issue_edge_token.side_effect = lambda _session, edge_id: f"signed-{edge_id}"
    presenter = SessionPresenter(graph, sessions)

    first = presenter.snapshot(session).relation_groups
    second = presenter.snapshot(session).relation_groups

    assert [group.property_id for group in first] == ["P36", "P36"]
    assert {(group.label, group.direction) for group in first} == {
        ("capital", "outgoing"),
        ("capital of", "incoming"),
    }
    assert len({group.group_id for group in first}) == 2
    assert [group.group_id for group in first] == [group.group_id for group in second]
    assert all(group.group_id.startswith(f"P36-{group.direction}-") for group in first)


def test_decision_history_preserves_every_fact_for_a_shared_target() -> None:
    entities = {
        "Q1": Entity("Q1", "Author", None, "person", "people"),
        "Q2": Entity("Q2", "Shared work", None, "work", "culture"),
        "Q3": Entity("Q3", "Alternative", None, "work", "culture"),
    }
    edges = (
        GraphEdge(
            id="edge-created",
            source_id="Q1",
            target_id="Q2",
            relation_key="P170",
            relation_label="creator of",
            statement_id="statement-created",
            explanation="Shared work was created by Author.",
            target=entities["Q2"],
            direction="incoming",
        ),
        GraphEdge(
            id="edge-notable",
            source_id="Q1",
            target_id="Q2",
            relation_key="P800",
            relation_label="notable work",
            statement_id="statement-notable",
            explanation="Author created Shared work.",
            target=entities["Q2"],
        ),
        GraphEdge(
            id="edge-alternative",
            source_id="Q1",
            target_id="Q3",
            relation_key="P737",
            relation_label="influenced by",
            statement_id="statement-alternative",
            explanation="Author was influenced by Alternative.",
            target=entities["Q3"],
        ),
    )
    round_ = Round(
        id="round-history",
        start_id="Q1",
        target_id="Q3",
        category="culture",
        difficulty=Difficulty.EASY,
        optimal_distance=2,
        time_window=120,
        published=True,
    )
    graph = MemoryGraphReader(
        entities=entities,
        edges=edges,
        rounds=(round_,),
        distances={
            (round_.id, "Q1"): 2,
            (round_.id, "Q2"): 1,
            (round_.id, "Q3"): 0,
        },
    )
    navigation = follow_edge(
        start_navigation("Q1"),
        edge_source_id="Q1",
        edge_target_id="Q2",
    )
    decision = followed_frame(
        source_id="Q1",
        destination_id="Q2",
        visible_edge_ids=tuple(edge.id for edge in edges),
        selected_edge_id="edge-notable",
    )
    session = GameSession(
        id="session-history",
        guest_id="guest",
        mode=SessionMode.SOLO,
        graph_version=graph.graph_version,
        round=round_,
        navigation=navigation,
        status=SessionStatus.ACTIVE,
        state_version=1,
        started_at=datetime(2026, 7, 14, tzinfo=UTC),
        decision_history=(
            decision,
            backed_frame(
                source_id="Q1",
                destination_id="Q1",
                visible_edge_ids=tuple(edge.id for edge in edges),
            ),
        ),
    )
    sessions = create_autospec(SessionService, instance=True)
    presenter = SessionPresenter(graph, sessions)

    first = presenter.snapshot(session).decision_history[0]
    second_snapshot = presenter.snapshot(session).decision_history
    second = second_snapshot[0]
    unselected_shared_target = next(
        choice for choice in second_snapshot[1].choices if choice.target.qid == "Q2"
    )
    shared_target = next(choice for choice in first.choices if choice.target.qid == "Q2")
    selected = next(choice for choice in first.choices if choice.id == first.selected_choice_id)

    assert len(first.choices) == 2
    assert {connection.statement for connection in shared_target.connections} == {
        "Shared work was created by Author.",
        "Author created Shared work.",
    }
    assert {connection.relation.property_id for connection in shared_target.connections} == {
        "P170",
        "P800",
    }
    assert len({choice.id for choice in first.choices}) == 2
    assert [connection.id for connection in shared_target.connections] == [
        connection.id
        for connection in next(
            choice for choice in second.choices if choice.target.qid == "Q2"
        ).connections
    ]
    assert selected.statement == "Author created Shared work."
    assert selected.relation.property_id == "P800"
    assert unselected_shared_target.statement == "Shared work was created by Author."
    assert unselected_shared_target.relation.property_id == "P170"
    assert "edge_token" not in selected.model_dump_json()
