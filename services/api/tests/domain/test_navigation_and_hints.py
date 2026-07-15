"""Navigation history and deterministic hint tests."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from webwoven_api.domain.errors import DomainError
from webwoven_api.domain.hints import (
    HintCandidate,
    HintOutcome,
    HintType,
    select_hint,
)
from webwoven_api.domain.navigation import NavigationState, follow_edge, go_back, start_navigation


def test_navigation_state_rejects_empty_or_cyclic_active_stacks() -> None:
    with pytest.raises(ValueError, match="stack cannot be empty"):
        NavigationState(stack=(), trail=("Q1",), moves=0)
    with pytest.raises(ValueError, match="stack must contain unique entities"):
        NavigationState(
            stack=("Q1", "Q2", "Q1"),
            trail=("Q1", "Q2", "Q1"),
            moves=2,
        )


def test_navigation_state_allows_repeated_entities_in_the_visible_trail() -> None:
    state = NavigationState(
        stack=("Q1", "Q2"),
        trail=("Q1", "Q2", "Q1", "Q2"),
        moves=3,
    )

    assert state.active_route_ids == frozenset({"Q1", "Q2"})
    assert state.trail == ("Q1", "Q2", "Q1", "Q2")


@given(
    st.lists(
        st.integers(min_value=1, max_value=10_000).map(lambda value: f"Q{value}"),
        min_size=1,
        max_size=30,
        unique=True,
    )
)
def test_follow_then_back_retains_visible_revisit(entity_ids: list[str]) -> None:
    state = start_navigation("start")
    for entity_id in entity_ids:
        state = follow_edge(
            state,
            edge_source_id=state.current_id,
            edge_target_id=entity_id,
        )
    before_trail = state.trail
    state = go_back(state)
    assert len(state.stack) == len(entity_ids)
    assert state.trail[:-1] == before_trail
    assert state.trail[-1] == state.current_id
    assert state.moves == len(entity_ids) + 1


def test_follow_rejects_an_entity_already_seen_in_the_route() -> None:
    initial = start_navigation("Q1")
    followed = follow_edge(initial, edge_source_id="Q1", edge_target_id="Q2")

    with pytest.raises(DomainError) as error:
        follow_edge(followed, edge_source_id="Q2", edge_target_id="Q1")

    assert error.value.code == "entity_already_in_route"
    assert followed.stack == ("Q1", "Q2")
    assert followed.trail == ("Q1", "Q2")
    assert followed.moves == 1
    returned = go_back(followed)
    assert returned.current_id == "Q1"
    assert "Q2" not in returned.active_route_ids


def test_back_at_start_is_rejected_without_mutation() -> None:
    state = start_navigation("Q1")
    with pytest.raises(DomainError, match="already at the start"):
        go_back(state)
    assert state.moves == 0


def test_lens_and_map_choose_stable_shortest_candidate() -> None:
    candidates = (
        HintCandidate("P50", "Q9", "Long way", 3),
        HintCandidate("P19", "Q2", "Bridge", 1),
        HintCandidate("P19", "Q3", "Another bridge", 1),
    )
    lens = select_hint(HintType.LENS, candidates)
    fragment = select_hint(HintType.MAP_FRAGMENT, candidates)
    assert lens.relation_key == "P19"
    assert lens.entity_id == "Q2"
    assert lens.outcome is HintOutcome.PROMISING
    assert fragment.entity_id == "Q2"
    assert fragment.penalty == 250


def test_compass_requires_a_specific_route() -> None:
    with pytest.raises(DomainError, match="Choose a specific route"):
        select_hint(HintType.COMPASS, (HintCandidate("P19", "Q2", "Bridge", 1),))


def test_compass_evaluates_exact_entities_in_a_shared_relation_group() -> None:
    candidates = (
        HintCandidate("P800", "Q2", "Useful work", 2),
        HintCandidate("P800", "Q3", "Closed work", None),
        HintCandidate("P19", "Q4", "Longer place", 4),
    )

    promising = select_hint(
        HintType.COMPASS,
        candidates,
        selected_relation_key="P800",
        selected_entity_id="Q2",
    )
    dead_end = select_hint(
        HintType.COMPASS,
        candidates,
        selected_relation_key="P800",
        selected_entity_id="Q3",
    )
    longer = select_hint(
        HintType.COMPASS,
        candidates,
        selected_relation_key="P19",
        selected_entity_id="Q4",
    )

    assert promising.entity_id == "Q2"
    assert promising.outcome is HintOutcome.PROMISING
    assert dead_end.entity_id == "Q3"
    assert dead_end.outcome is HintOutcome.DEAD_END
    assert "dead end" in dead_end.message
    assert longer.outcome is HintOutcome.LONGER
