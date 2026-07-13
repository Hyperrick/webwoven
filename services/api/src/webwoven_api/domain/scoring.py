"""Pure Route Race score calculation."""

from dataclasses import dataclass
from enum import StrEnum


class Difficulty(StrEnum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


TIME_WINDOWS: dict[Difficulty, int] = {
    Difficulty.EASY: 120,
    Difficulty.NORMAL: 180,
    Difficulty.HARD: 240,
}


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    total: int
    efficiency: float
    speed: float
    hint_penalty: int


def calculate_score(
    shortest_distance: int,
    moves: int,
    elapsed_seconds: float,
    time_window: int,
    hint_penalty: int = 0,
) -> ScoreBreakdown:
    """Return the documented 80% efficiency / 20% speed score."""
    if shortest_distance < 1:
        raise ValueError("shortest_distance must be positive")
    if moves < 0:
        raise ValueError("moves cannot be negative")
    if elapsed_seconds < 0:
        raise ValueError("elapsed_seconds cannot be negative")
    if time_window < 1:
        raise ValueError("time_window must be positive")
    if hint_penalty < 0:
        raise ValueError("hint_penalty cannot be negative")

    efficiency = shortest_distance / max(moves, shortest_distance)
    speed = max(0.0, 1.0 - elapsed_seconds / time_window)
    unpenalized = round(1000 * (0.8 * efficiency + 0.2 * speed))
    total = min(1000, max(0, unpenalized - hint_penalty))
    return ScoreBreakdown(
        total=total,
        efficiency=efficiency,
        speed=speed,
        hint_penalty=hint_penalty,
    )
