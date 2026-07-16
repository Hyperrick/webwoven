"""History-aware selection cycles and repeat avoidance."""

from webwoven_api.domain.scoring import TIME_WINDOWS, Difficulty
from webwoven_api.graph.contracts import Round
from webwoven_api.sessions.selection import choose_round


def _round(round_id: str) -> Round:
    return Round(
        id=round_id,
        start_id="Q1",
        target_id="Q2",
        category="people",
        difficulty=Difficulty.NORMAL,
        optimal_distance=1,
        time_window=TIME_WINDOWS[Difficulty.NORMAL],
        published=True,
    )


def test_selects_unseen_rounds_before_starting_a_new_cycle() -> None:
    rounds = tuple(_round(round_id) for round_id in ("a", "b", "c"))
    selected = choose_round(rounds, ("a", "c"), lambda choices: choices[0])
    assert selected.id == "b"


def test_new_cycle_excludes_immediately_previous_round() -> None:
    rounds = tuple(_round(round_id) for round_id in ("a", "b", "c"))
    selected = choose_round(rounds, ("a", "b", "c"), lambda choices: choices[0])
    assert selected.id == "a"


def test_single_round_pool_can_repeat() -> None:
    only = _round("only")
    assert choose_round((only,), ("only",), lambda choices: choices[0]) is only


def test_legacy_early_repeat_starts_a_recoverable_cycle() -> None:
    rounds = tuple(_round(round_id) for round_id in ("a", "b", "c"))
    selected = choose_round(rounds, ("a", "a", "b"), lambda choices: choices[0])
    assert selected.id == "c"
