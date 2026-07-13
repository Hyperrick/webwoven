"""Navigation history and deterministic hint tests."""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from webwoven_api.domain.errors import DomainError
from webwoven_api.domain.hints import HintCandidate, HintType, select_hint
from webwoven_api.domain.navigation import follow_edge, go_back, start_navigation


@given(st.lists(st.text(min_size=1), min_size=1, max_size=30))
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
    assert fragment.entity_id == "Q2"
    assert fragment.penalty == 250


def test_compass_requires_a_selected_group() -> None:
    with pytest.raises(DomainError, match="Choose a relationship"):
        select_hint(HintType.COMPASS, (HintCandidate("P19", "Q2", "Bridge", 1),))
