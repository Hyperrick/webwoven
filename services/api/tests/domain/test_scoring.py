"""Property tests for score bounds and monotonic behavior."""

from hypothesis import given
from hypothesis import strategies as st
from webwoven_api.domain.scoring import calculate_score


@given(
    shortest=st.integers(min_value=1, max_value=50),
    moves=st.integers(min_value=0, max_value=500),
    elapsed=st.floats(min_value=0, max_value=10_000, allow_nan=False),
    window=st.integers(min_value=1, max_value=500),
    penalty=st.integers(min_value=0, max_value=2_000),
)
def test_score_is_always_bounded(
    shortest: int,
    moves: int,
    elapsed: float,
    window: int,
    penalty: int,
) -> None:
    score = calculate_score(shortest, moves, elapsed, window, penalty)
    assert 0 <= score.total <= 1000
    assert 0 <= score.efficiency <= 1
    assert 0 <= score.speed <= 1


@given(
    shortest=st.integers(min_value=1, max_value=30),
    moves=st.integers(min_value=1, max_value=300),
    early=st.floats(min_value=0, max_value=500, allow_nan=False),
    delay=st.floats(min_value=0, max_value=500, allow_nan=False),
)
def test_waiting_longer_never_improves_score(
    shortest: int, moves: int, early: float, delay: float
) -> None:
    first = calculate_score(shortest, moves, early, 180)
    later = calculate_score(shortest, moves, early + delay, 180)
    assert later.total <= first.total


@given(
    shortest=st.integers(min_value=1, max_value=30),
    first_moves=st.integers(min_value=1, max_value=200),
    extra_moves=st.integers(min_value=0, max_value=200),
)
def test_extra_moves_never_improve_score(shortest: int, first_moves: int, extra_moves: int) -> None:
    first = calculate_score(shortest, first_moves, 20, 180)
    later = calculate_score(shortest, first_moves + extra_moves, 20, 180)
    assert later.total <= first.total
